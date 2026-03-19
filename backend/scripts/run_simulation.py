"""
国内舆情平台模拟预设脚本
此脚本读取配置文件中的参数来执行模拟，实现全程自动化

功能特性:
- 完成模拟后不立即关闭环境，进入等待命令模式
- 支持通过IPC接收Interview命令
- 支持单个Agent采访和批量采访
- 支持远程关闭环境命令

使用方式:
    python run_simulation.py --config /path/to/simulation_config.json
    python run_simulation.py --config /path/to/simulation_config.json --no-wait  # 完成后立即关闭
"""

# -*- coding: utf-8 -*-
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
import asyncio
import json
import logging
import os
import random
import signal
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

_scripts_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.abspath(os.path.join(_scripts_dir, '..'))
_project_root = os.path.abspath(os.path.join(_backend_dir, '..'))
sys.path.insert(0, _scripts_dir)
sys.path.insert(0, _backend_dir)

from dotenv import load_dotenv
_env_file = os.path.join(_project_root, '.env')
if os.path.exists(_env_file):
    load_dotenv(_env_file)
else:
    _backend_env = os.path.join(_backend_dir, '.env')
    if os.path.exists(_backend_env):
        load_dotenv(_backend_env)


import re


class UnicodeFormatter(logging.Formatter):
    UNICODE_ESCAPE_PATTERN = re.compile(r'\\u([0-9a-fA-F]{4})')

    def format(self, record):
        result = super().format(record)

        def replace_unicode(match):
            try:
                return chr(int(match.group(1), 16))
            except (ValueError, OverflowError):
                return match.group(0)

        return self.UNICODE_ESCAPE_PATTERN.sub(replace_unicode, result)


class MaxTokensWarningFilter(logging.Filter):
    def filter(self, record):
        if "max_tokens" in record.getMessage() and "Invalid or missing" in record.getMessage():
            return False
        return True


logging.getLogger().addFilter(MaxTokensWarningFilter())


def setup_oasis_logging(log_dir: str):
    os.makedirs(log_dir, exist_ok=True)

    for f in os.listdir(log_dir):
        old_log = os.path.join(log_dir, f)
        if os.path.isfile(old_log) and f.endswith('.log'):
            try:
                os.remove(old_log)
            except OSError:
                pass

    formatter = UnicodeFormatter("%(levelname)s - %(asctime)s - %(name)s - %(message)s")

    loggers_config = {
        "social.agent": os.path.join(log_dir, "social.agent.log"),
        "social.twitter": os.path.join(log_dir, "social.agent.log"),
        "social.rec": os.path.join(log_dir, "social.rec.log"),
        "oasis.env": os.path.join(log_dir, "oasis.env.log"),
        "table": os.path.join(log_dir, "table.log"),
    }

    for logger_name, log_file in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='w', errors='replace')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.propagate = False


try:
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType
    import oasis
    from oasis import (
        ActionType,
        LLMAction,
        ManualAction,
        generate_reddit_agent_graph
    )
except ImportError as e:
    print(f"错误: 缺少依赖 {e}")
    print("请先安装: pip install camel-oasis camel-ai")
    sys.exit(1)


IPC_COMMANDS_DIR = "ipc_commands"
IPC_RESPONSES_DIR = "ipc_responses"
ENV_STATUS_FILE = "env_status.json"


class CommandType:
    INTERVIEW = "interview"
    BATCH_INTERVIEW = "batch_interview"
    CLOSE_ENV = "close_env"


class IPCHandler:
    def __init__(self, simulation_dir: str, env, agent_graph):
        self.simulation_dir = simulation_dir
        self.env = env
        self.agent_graph = agent_graph
        self.commands_dir = os.path.join(simulation_dir, IPC_COMMANDS_DIR)
        self.responses_dir = os.path.join(simulation_dir, IPC_RESPONSES_DIR)
        self.status_file = os.path.join(simulation_dir, ENV_STATUS_FILE)
        self._running = True

        os.makedirs(self.commands_dir, exist_ok=True)
        os.makedirs(self.responses_dir, exist_ok=True)

    def update_status(self, status: str):
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": status,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)

    def poll_command(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.commands_dir):
            return None

        command_files = []
        for filename in os.listdir(self.commands_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.commands_dir, filename)
                command_files.append((filepath, os.path.getmtime(filepath)))

        command_files.sort(key=lambda x: x[1])

        for filepath, _ in command_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

        return None

    def send_response(self, command_id: str, status: str, result: Dict = None, error: str = None):
        response = {
            "command_id": command_id,
            "status": status,
            "result": result,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }

        response_file = os.path.join(self.responses_dir, f"{command_id}.json")
        with open(response_file, 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=2)

        command_file = os.path.join(self.commands_dir, f"{command_id}.json")
        try:
            os.remove(command_file)
        except OSError:
            pass

    async def handle_interview(self, command_id: str, agent_id: int, prompt: str) -> bool:
        try:
            agent = self.agent_graph.get_agent(agent_id)

            interview_action = ManualAction(
                action_type=ActionType.INTERVIEW,
                action_args={"prompt": prompt}
            )

            actions = {agent: interview_action}
            await self.env.step(actions)

            result = self._get_interview_result(agent_id)

            self.send_response(command_id, "completed", result=result)
            print(f"  Interview完成: agent_id={agent_id}")
            return True

        except Exception as e:
            error_msg = str(e)
            print(f"  Interview失败: agent_id={agent_id}, error={error_msg}")
            self.send_response(command_id, "failed", error=error_msg)
            return False

    async def handle_batch_interview(self, command_id: str, interviews: List[Dict]) -> bool:
        try:
            actions = {}
            agent_prompts = {}

            for interview in interviews:
                agent_id = interview.get("agent_id")
                prompt = interview.get("prompt", "")

                try:
                    agent = self.agent_graph.get_agent(agent_id)
                    actions[agent] = ManualAction(
                        action_type=ActionType.INTERVIEW,
                        action_args={"prompt": prompt}
                    )
                    agent_prompts[agent_id] = prompt
                except Exception as e:
                    print(f"  警告: 无法获取Agent {agent_id}: {e}")

            if not actions:
                self.send_response(command_id, "failed", error="没有有效的Agent")
                return False

            await self.env.step(actions)

            results = {}
            for agent_id in agent_prompts.keys():
                result = self._get_interview_result(agent_id)
                results[agent_id] = result

            self.send_response(command_id, "completed", result={
                "interviews_count": len(results),
                "results": results
            })
            print(f"  批量Interview完成: {len(results)} 个Agent")
            return True

        except Exception as e:
            error_msg = str(e)
            print(f"  批量Interview失败: {error_msg}")
            self.send_response(command_id, "failed", error=error_msg)
            return False

    def _get_interview_result(self, agent_id: int) -> Dict[str, Any]:
        db_path = os.path.join(self.simulation_dir, "simulation.db")

        result = {
            "agent_id": agent_id,
            "response": None,
            "timestamp": None
        }

        if not os.path.exists(db_path):
            return result

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT user_id, info, created_at
                FROM trace
                WHERE action = ? AND user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (ActionType.INTERVIEW.value, agent_id))

            row = cursor.fetchone()
            if row:
                user_id, info_json, created_at = row
                try:
                    info = json.loads(info_json) if info_json else {}
                    result["response"] = info.get("response", info)
                    result["timestamp"] = created_at
                except json.JSONDecodeError:
                    result["response"] = info_json

            conn.close()

        except Exception as e:
            print(f"  读取Interview结果失败: {e}")

        return result

    async def process_commands(self) -> bool:
        command = self.poll_command()
        if not command:
            return True

        command_id = command.get("command_id")
        command_type = command.get("command_type")
        args = command.get("args", {})

        print(f"\n收到IPC命令: {command_type}, id={command_id}")

        if command_type == CommandType.INTERVIEW:
            await self.handle_interview(
                command_id,
                args.get("agent_id", 0),
                args.get("prompt", "")
            )
            return True

        elif command_type == CommandType.BATCH_INTERVIEW:
            await self.handle_batch_interview(
                command_id,
                args.get("interviews", [])
            )
            return True

        elif command_type == CommandType.CLOSE_ENV:
            print("收到关闭环境命令")
            self.send_response(command_id, "completed", result={"message": "环境即将关闭"})
            return False

        else:
            self.send_response(command_id, "failed", error=f"未知命令类型: {command_type}")
            return True


class SimulationRunner:
    """国内舆情平台模拟运行器"""

    AVAILABLE_ACTIONS = [
        ActionType.LIKE_POST,
        ActionType.DISLIKE_POST,
        ActionType.CREATE_POST,
        ActionType.CREATE_COMMENT,
        ActionType.LIKE_COMMENT,
        ActionType.DISLIKE_COMMENT,
        ActionType.SEARCH_POSTS,
        ActionType.SEARCH_USER,
        ActionType.TREND,
        ActionType.REFRESH,
        ActionType.DO_NOTHING,
        ActionType.FOLLOW,
        ActionType.MUTE,
    ]

    def __init__(self, config_path: str, wait_for_commands: bool = True):
        self.config_path = config_path
        self.config = self._load_config()
        self.simulation_dir = os.path.dirname(config_path)
        self.wait_for_commands = wait_for_commands
        self.env = None
        self.agent_graph = None
        self.ipc_handler = None

    def _load_config(self) -> Dict[str, Any]:
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _get_profile_path(self) -> str:
        return os.path.join(self.simulation_dir, "reddit_profiles.json")

    def _get_db_path(self) -> str:
        return os.path.join(self.simulation_dir, "simulation.db")

    def _create_model(self):
        llm_api_key = os.environ.get("LLM_API_KEY", "")
        llm_base_url = os.environ.get("LLM_BASE_URL", "")
        llm_model = os.environ.get("LLM_MODEL_NAME", "")

        if not llm_model:
            llm_model = self.config.get("llm_model", "gpt-4o-mini")

        if llm_api_key:
            os.environ["OPENAI_API_KEY"] = llm_api_key

        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("缺少 API Key 配置，请在项目根目录 .env 文件中设置 LLM_API_KEY")

        if llm_base_url:
            os.environ["OPENAI_API_BASE_URL"] = llm_base_url

        print(f"LLM配置: model={llm_model}, base_url={llm_base_url[:40] if llm_base_url else '默认'}...")

        boost_api_key = os.environ.get("LLM_BOOST_API_KEY", "")
        boost_base_url = os.environ.get("LLM_BOOST_BASE_URL", "")
        boost_model = os.environ.get("LLM_BOOST_MODEL_NAME", "")

        if boost_api_key:
            print(f"检测到加速LLM配置，将使用加速服务")
            os.environ["OPENAI_API_KEY"] = boost_api_key
            if boost_base_url:
                os.environ["OPENAI_API_BASE_URL"] = boost_base_url
            llm_model = boost_model or llm_model
            print(f"加速LLM: model={llm_model}")

        return ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=llm_model,
        )

    def _get_active_agents_for_round(
        self,
        env,
        current_hour: int,
        round_num: int
    ) -> List:
        time_config = self.config.get("time_config", {})
        agent_configs = self.config.get("agent_configs", [])

        base_min = time_config.get("agents_per_hour_min", 5)
        base_max = time_config.get("agents_per_hour_max", 20)

        peak_hours = time_config.get("peak_hours", [9, 10, 11, 14, 15, 20, 21, 22])
        off_peak_hours = time_config.get("off_peak_hours", [0, 1, 2, 3, 4, 5])

        if current_hour in peak_hours:
            multiplier = time_config.get("peak_activity_multiplier", 1.5)
        elif current_hour in off_peak_hours:
            multiplier = time_config.get("off_peak_activity_multiplier", 0.3)
        else:
            multiplier = 1.0

        target_count = int(random.uniform(base_min, base_max) * multiplier)

        candidates = []
        for cfg in agent_configs:
            agent_id = cfg.get("agent_id", 0)
            active_hours = cfg.get("active_hours", list(range(8, 23)))
            activity_level = cfg.get("activity_level", 0.5)

            if current_hour not in active_hours:
                continue

            if random.random() < activity_level:
                candidates.append(agent_id)

        selected_ids = random.sample(
            candidates,
            min(target_count, len(candidates))
        ) if candidates else []

        active_agents = []
        for agent_id in selected_ids:
            try:
                agent = env.agent_graph.get_agent(agent_id)
                active_agents.append((agent_id, agent))
            except Exception:
                pass

        return active_agents

    async def run(self, max_rounds: int = None):
        print("=" * 60)
        print("国内舆情平台模拟")
        print(f"配置文件: {self.config_path}")
        print(f"模拟ID: {self.config.get('simulation_id', 'unknown')}")
        print(f"等待命令模式: {'启用' if self.wait_for_commands else '禁用'}")
        print("=" * 60)

        time_config = self.config.get("time_config", {})
        total_hours = time_config.get("total_simulation_hours", 72)
        minutes_per_round = time_config.get("minutes_per_round", 30)
        total_rounds = (total_hours * 60) // minutes_per_round

        if max_rounds is not None and max_rounds > 0:
            original_rounds = total_rounds
            total_rounds = min(total_rounds, max_rounds)
            if total_rounds < original_rounds:
                print(f"\n轮数已截断: {original_rounds} -> {total_rounds} (max_rounds={max_rounds})")

        print(f"\n模拟参数:")
        print(f"  - 总模拟时长: {total_hours}小时")
        print(f"  - 每轮时间: {minutes_per_round}分钟")
        print(f"  - 总轮数: {total_rounds}")
        if max_rounds:
            print(f"  - 最大轮数限制: {max_rounds}")
        print(f"  - Agent数量: {len(self.config.get('agent_configs', []))}")

        print("\n初始化LLM模型...")
        model = self._create_model()

        print("加载Agent Profile...")
        profile_path = self._get_profile_path()
        if not os.path.exists(profile_path):
            print(f"错误: Profile文件不存在: {profile_path}")
            return

        self.agent_graph = await generate_reddit_agent_graph(
            profile_path=profile_path,
            model=model,
            available_actions=self.AVAILABLE_ACTIONS,
        )

        db_path = self._get_db_path()
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"已删除旧数据库: {db_path}")

        print("创建OASIS环境...")
        self.env = oasis.make(
            agent_graph=self.agent_graph,
            platform=oasis.DefaultPlatformType.REDDIT,
            database_path=db_path,
            semaphore=30,
        )

        await self.env.reset()
        print("环境初始化完成\n")

        self.ipc_handler = IPCHandler(
            simulation_dir=self.simulation_dir,
            env=self.env,
            agent_graph=self.agent_graph
        )
        self.ipc_handler.update_status("running")

        log_dir = os.path.join(self.simulation_dir, "logs")
        setup_oasis_logging(log_dir)

        # 初始化动作日志记录器
        from action_logger import SimulationLogManager
        log_manager = SimulationLogManager(self.simulation_dir)
        twitter_logger = log_manager.get_twitter_logger()
        reddit_logger = log_manager.get_reddit_logger()
        
        # 记录模拟开始
        twitter_logger.log_simulation_start(self.config)
        reddit_logger.log_simulation_start(self.config)

        current_hour = 0
        completed_rounds = 0

        try:
            print("\n开始模拟...\n", flush=True)

            for round_num in range(total_rounds):
                round_start_time = datetime.now()

                print(f"[轮次 {round_num + 1}/{total_rounds}]", flush=True)
                
                # 记录轮次开始
                twitter_logger.log_round_start(round_num + 1, current_hour)
                reddit_logger.log_round_start(round_num + 1, current_hour)

                active_agents = self._get_active_agents_for_round(
                    self.env, current_hour, round_num
                )

                if not active_agents:
                    print("无活跃Agent，跳过", flush=True)
                    
                    # 记录轮次结束（无动作）
                    twitter_logger.log_round_end(round_num + 1, 0, current_hour)
                    reddit_logger.log_round_end(round_num + 1, 0, current_hour)
                    
                    current_hour = (current_hour + 1) % 24

                    if not self.wait_for_commands:
                        continue
                    else:
                        if not await self.ipc_handler.process_commands():
                            print("IPC命令结束模拟", flush=True)
                            break
                        continue

                print(f"活跃Agent: {len(active_agents)}", flush=True)

                actions = {}
                for agent_id, agent in active_agents:
                    action = LLMAction()
                    actions[agent] = action

                actions_count = 0
                try:
                    await self.env.step(actions)
                    # 统计动作数量（这里简化处理，实际应该从环境返回中获取）
                    actions_count = len(actions)
                except Exception as e:
                    print(f"  模拟步骤出错: {e}")

                if self.wait_for_commands:
                    if not await self.ipc_handler.process_commands():
                        print("IPC命令结束模拟")
                        break

                # 记录轮次结束
                twitter_logger.log_round_end(round_num + 1, actions_count, current_hour)
                reddit_logger.log_round_end(round_num + 1, actions_count, current_hour)

                current_hour = (current_hour + 1) % 24
                completed_rounds += 1

                round_elapsed = (datetime.now() - round_start_time).total_seconds()
                print(f"  耗时: {round_elapsed:.1f}秒", flush=True)

        except KeyboardInterrupt:
            print("\n\n收到中断信号，正在停止模拟...", flush=True)

        finally:
            self.ipc_handler.update_status("completed")
            # 记录模拟结束
            twitter_logger.log_simulation_end(completed_rounds, completed_rounds * 3)  # 估算动作数
            reddit_logger.log_simulation_end(completed_rounds, completed_rounds * 3)
            print(f"\n模拟完成: {completed_rounds}/{total_rounds} 轮", flush=True)
            print(f"数据库: {db_path}", flush=True)


def signal_handler(signum, frame):
    global _shutdown_event
    print("\n收到信号，正在清理...")
    if _shutdown_event:
        _shutdown_event.set()


def main():
    global _shutdown_event

    parser = argparse.ArgumentParser(description="国内舆情平台模拟")
    parser.add_argument("--config", required=True, help="配置文件路径")
    parser.add_argument("--no-wait", action="store_true", help="模拟完成后立即关闭")
    parser.add_argument("--max-rounds", type=int, default=None, help="最大模拟轮数")
    args = parser.parse_args()

    _shutdown_event = asyncio.Event()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if not os.path.exists(args.config):
        print(f"错误: 配置文件不存在: {args.config}")
        return 1

    runner = SimulationRunner(
        config_path=args.config,
        wait_for_commands=not args.no_wait
    )

    try:
        asyncio.run(runner.run(max_rounds=args.max_rounds))
    except Exception as e:
        print(f"模拟出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())