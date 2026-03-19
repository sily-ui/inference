"""
Prediction Agent服务
使用ReACT模式实现舆情预测的智能体架构

功能：
1. 规划阶段：分析舆情事件特征，制定预测策略
2. 执行阶段：通过ReACT循环调用工具进行分析
3. 反思阶段：检查预测合理性，生成最终结论

工具系统：
- sir_model_analyzer: SIR传播模型分析
- bayesian_predictor: 贝叶斯情景预测
- sentiment_analyzer: 情绪趋势分析
- risk_assessor: 风险节点评估
- intervention_simulator: 干预策略模拟
"""

import os
import json
import time
import re
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import Config
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from .algorithm_engine import AlgorithmEngine

logger = get_logger("mirofish.prediction_agent")


class PredictionStage(Enum):
    """预测阶段"""
    PENDING = "pending"
    PLANNING = "planning"
    ANALYZING = "analyzing"
    PREDICTING = "predicting"
    REFLECTING = "reflecting"
    COMPLETED = "completed"


class PredictionLogger:
    """
    Prediction Agent 详细日志记录器

    在预测文件夹中生成 agent_log.jsonl 文件，记录每一步详细动作。
    每行是一个完整的 JSON 对象，包含时间戳、动作类型、详细内容等。
    """

    def __init__(self, prediction_id: str):
        self.prediction_id = prediction_id
        self.log_file_path = os.path.join(
            Config.UPLOAD_FOLDER, "predictions", prediction_id, "agent_log.jsonl"
        )
        self.start_time = datetime.now()
        self._ensure_log_file()

    def _ensure_log_file(self):
        log_dir = os.path.dirname(self.log_file_path)
        os.makedirs(log_dir, exist_ok=True)

    def _get_elapsed_time(self) -> float:
        return (datetime.now() - self.start_time).total_seconds()

    def log(
        self,
        action: str,
        stage: str,
        details: Dict[str, Any],
        module_name: str = None,
        module_index: int = None,
    ):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": round(self._get_elapsed_time(), 2),
            "prediction_id": self.prediction_id,
            "action": action,
            "stage": stage,
            "module_name": module_name,
            "module_index": module_index,
            "details": details,
        }

        with open(self.log_file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def log_start(self, simulation_id: str, event_summary: str):
        self.log(
            action="prediction_start",
            stage="pending",
            details={
                "simulation_id": simulation_id,
                "event_summary": event_summary[:200] if event_summary else "",
                "message": "舆情预测任务开始",
            },
        )

    def log_planning_start(self):
        self.log(
            action="planning_start",
            stage="planning",
            details={"message": "开始规划预测策略"},
        )

    def log_planning_thought(self, thought: str):
        self.log(
            action="planning_thought",
            stage="planning",
            details={"thought": thought, "message": "规划思考"},
        )

    def log_planning_complete(self, plan: Dict[str, Any]):
        self.log(
            action="planning_complete",
            stage="planning",
            details={"message": "预测策略规划完成", "plan": plan},
        )

    def log_module_start(self, module_name: str, module_index: int):
        self.log(
            action="module_start",
            stage="analyzing",
            module_name=module_name,
            module_index=module_index,
            details={"message": f"开始分析模块: {module_name}"},
        )

    def log_react_thought(
        self, module_name: str, module_index: int, iteration: int, thought: str
    ):
        self.log(
            action="react_thought",
            stage="analyzing",
            module_name=module_name,
            module_index=module_index,
            details={
                "iteration": iteration,
                "thought": thought,
                "message": f"ReACT 第{iteration}轮思考",
            },
        )

    def log_tool_call(
        self,
        module_name: str,
        module_index: int,
        tool_name: str,
        parameters: Dict[str, Any],
        iteration: int,
    ):
        self.log(
            action="tool_call",
            stage="analyzing",
            module_name=module_name,
            module_index=module_index,
            details={
                "iteration": iteration,
                "tool_name": tool_name,
                "parameters": parameters,
                "message": f"调用工具: {tool_name}",
            },
        )

    def log_tool_result(
        self,
        module_name: str,
        module_index: int,
        tool_name: str,
        result: Any,
        iteration: int,
    ):
        result_str = json.dumps(result, ensure_ascii=False) if isinstance(result, (dict, list)) else str(result)
        self.log(
            action="tool_result",
            stage="analyzing",
            module_name=module_name,
            module_index=module_index,
            details={
                "iteration": iteration,
                "tool_name": tool_name,
                "result": result_str[:2000] if len(result_str) > 2000 else result_str,
                "result_length": len(result_str),
                "message": f"工具 {tool_name} 返回结果",
            },
        )

    def log_llm_response(
        self,
        module_name: str,
        module_index: int,
        response: str,
        iteration: int,
        has_tool_calls: bool,
        has_final_answer: bool,
    ):
        self.log(
            action="llm_response",
            stage="analyzing",
            module_name=module_name,
            module_index=module_index,
            details={
                "iteration": iteration,
                "response": response[:1500] if len(response) > 1500 else response,
                "response_length": len(response),
                "has_tool_calls": has_tool_calls,
                "has_final_answer": has_final_answer,
                "message": f"LLM 响应 (工具调用: {has_tool_calls}, 最终答案: {has_final_answer})",
            },
        )

    def log_module_complete(
        self, module_name: str, module_index: int, result: Dict[str, Any]
    ):
        self.log(
            action="module_complete",
            stage="analyzing",
            module_name=module_name,
            module_index=module_index,
            details={
                "result": result,
                "message": f"模块 {module_name} 分析完成",
            },
        )

    def log_reflection_start(self):
        self.log(
            action="reflection_start",
            stage="reflecting",
            details={"message": "开始反思预测结果"},
        )

    def log_reflection_result(self, conclusion: str, confidence: float):
        self.log(
            action="reflection_result",
            stage="reflecting",
            details={
                "conclusion": conclusion,
                "confidence": confidence,
                "message": "反思完成，生成最终结论",
            },
        )

    def log_prediction_complete(self, total_time_seconds: float):
        self.log(
            action="prediction_complete",
            stage="completed",
            details={
                "total_time_seconds": round(total_time_seconds, 2),
                "message": "舆情预测完成",
            },
        )

    def log_error(self, error_message: str, stage: str, module_name: str = None):
        self.log(
            action="error",
            stage=stage,
            module_name=module_name,
            module_index=None,
            details={"error": error_message, "message": f"发生错误: {error_message}"},
        )


PLANNING_SYSTEM_PROMPT = """你是一位资深的舆情预测专家。现在需要为一个舆情事件制定预测分析策略。

你需要分析事件特征，并规划接下来的预测步骤。

可用分析工具：
1. sir_model_analyzer - SIR传播模型，分析舆情传播趋势和热度变化
2. bayesian_predictor - 贝叶斯网络预测，生成多情景概率分布
3. sentiment_analyzer - 情绪趋势分析，分析情绪走向和关键转折点
4. risk_assessor - 风险节点评估，识别高风险时间点和因素
5. intervention_simulator - 干预策略模拟，评估干预措施效果

请根据事件特点，制定预测策略。输出JSON格式：
{
    "event_type": "事件类型（product_issue/company_crisis/public_safety/celebrity/policy/social/general）",
    "event_features": ["特征1", "特征2"],
    "analysis_plan": [
        {"tool": "工具名", "reason": "使用原因", "priority": 1},
        {"tool": "工具名", "reason": "使用原因", "priority": 2}
    ],
    "key_questions": ["需要回答的关键问题1", "关键问题2"],
    "risk_focus": ["需要重点关注的风险点"]
}

只输出JSON，不要其他解释。"""

ANALYSIS_SYSTEM_PROMPT = """你是一位舆情预测专家，正在使用ReACT模式分析舆情数据。

可用工具：
1. sir_model_analyzer - SIR传播模型分析
   参数: {{"event_summary": "事件摘要", "current_sentiment": "情绪", "days": 天数}}

2. bayesian_predictor - 贝叶斯情景预测
   参数: {{"event_summary": "事件摘要", "current_sentiment": "情绪"}}

3. sentiment_analyzer - 情绪趋势分析
   参数: {{"event_summary": "事件摘要", "timeline": 时间轴数据}}

4. risk_assessor - 风险节点评估
   参数: {{"timeline": 时间轴数据, "scenarios": 情景数据}}

5. intervention_simulator - 干预策略模拟
   参数: {{"event_summary": "事件摘要", "intervention": "干预措施", "current_sentiment": "情绪"}}

ReACT循环规则：
1. Thought: 思考当前需要什么信息
2. Action: 调用一个工具（使用 <tool_call name="工具名">{"参数": "值"}</tool_callcall> 格式）
3. Observation: 系统返回工具结果
4. 重复直到信息充分
5. Final Answer: 输出最终分析结果

重要规则：
- 每次只能调用一个工具
- 工具调用和Final Answer不能同时出现
- 至少调用2个工具后才能输出Final Answer
- 最多调用5次工具

输出格式：
Thought: 我的思考...
<tool_call name="工具名">
{"参数名": "参数值"}
</tool_callcall>

或（信息充分时）：
Final Answer: 最终分析结果..."""

REFLECTION_SYSTEM_PROMPT = """你是一位舆情分析专家，需要对预测结果进行反思和总结。

请检查预测结果的合理性，并生成最终结论。

要求：
1. 检查各模块结果的一致性
2. 评估预测的可信度
3. 提炼核心洞察
4. 给出行动建议

输出JSON格式：
{
    "confidence": 0.85,
    "consistency_check": "各模块结果一致性评估",
    "key_insights": ["核心洞察1", "核心洞察2"],
    "action_suggestions": ["建议1", "建议2"],
    "final_conclusion": "最终结论（100-150字）"
}

只输出JSON，不要其他解释。"""


REACT_INSUFFICIENT_TOOLS_MSG = """你已经调用了 {tool_calls_count} 次工具，但至少需要调用 {min_tool_calls} 次才能得出可靠结论。
{unused_hint}
请继续调用工具获取更多信息，然后再输出 Final Answer。"""

REACT_TOOL_LIMIT_MSG = """你已经达到了最大工具调用次数 {max_tool_calls} 次。
请基于已有信息，输出 Final Answer。"""

REACT_OBSERVATION_TEMPLATE = """工具 {tool_name} 返回结果：
{result}

已调用工具次数: {tool_calls_count}/{max_tool_calls}
已使用工具: {used_tools_str}
{unused_hint}

请继续分析，或输出 Final Answer。"""

REACT_UNUSED_TOOLS_HINT = "\n（还有未使用的工具: {unused_list}，建议使用）"


class PredictionAgent:
    """
    Prediction Agent - 舆情预测智能体

    采用ReACT（Reasoning + Acting）模式：
    1. 规划阶段：分析事件特征，制定预测策略
    2. 分析阶段：通过ReACT循环调用工具进行分析
    3. 反思阶段：检查预测合理性，生成最终结论
    """

    MAX_TOOL_CALLS_PER_MODULE = 5
    MIN_TOOL_CALLS_PER_MODULE = 2

    def __init__(
        self,
        simulation_id: str = None,
        event_summary: str = "",
        current_sentiment: str = "中性",
        time_range: int = 7,
        simulation_data: Dict[str, Any] = None,
    ):
        self.simulation_id = simulation_id
        self.event_summary = event_summary
        self.current_sentiment = current_sentiment
        self.time_range = time_range
        self.simulation_data = simulation_data or {}

        self.llm = LLMClient()
        self.algorithm_engine = AlgorithmEngine()
        self.prediction_logger: Optional[PredictionLogger] = None

        self.analysis_plan = []
        self.analysis_results = {}

    def predict(
        self,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        执行完整预测流程

        Args:
            progress_callback: 进度回调函数 (stage, progress, message)

        Returns:
            完整预测结果
        """
        start_time = time.time()
        prediction_id = f"pred_{int(time.time() * 1000)}"

        self.prediction_logger = PredictionLogger(prediction_id)
        self.prediction_logger.log_start(self.simulation_id or "", self.event_summary)

        try:
            if progress_callback:
                progress_callback("planning", 5, "开始规划预测策略...")

            plan = self._plan_strategy(progress_callback)
            self.analysis_plan = plan.get("analysis_plan", [])

            if progress_callback:
                progress_callback("analyzing", 20, "开始深度分析...")

            results = self._execute_analysis(progress_callback)

            if progress_callback:
                progress_callback("reflecting", 85, "反思预测结果...")

            conclusion = self._reflect_and_conclude(results, progress_callback)

            total_time = time.time() - start_time
            self.prediction_logger.log_prediction_complete(total_time)

            if progress_callback:
                progress_callback("completed", 100, "预测完成")

            return {
                "prediction_id": prediction_id,
                "simulation_id": self.simulation_id,
                "event_summary": self.event_summary,
                "current_sentiment": self.current_sentiment,
                "time_range": self.time_range,
                "generated_at": datetime.now().isoformat(),
                "plan": plan,
                "timeline": results.get("timeline", []),
                "scenarios": results.get("scenarios", []),
                "scenario_summary": results.get("scenario_summary", ""),
                "warnings": results.get("warnings", []),
                "visualization": results.get("visualization", {}),
                "conclusion": conclusion.get("final_conclusion", ""),
                "confidence": conclusion.get("confidence", 0.8),
                "key_insights": conclusion.get("key_insights", []),
                "action_suggestions": conclusion.get("action_suggestions", []),
            }

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            if self.prediction_logger:
                self.prediction_logger.log_error(str(e), "analyzing")
            return self._generate_fallback_result()

    def _plan_strategy(
        self, progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """规划预测策略"""
        self.prediction_logger.log_planning_start()

        user_prompt = f"""请为以下舆情事件制定预测分析策略：

事件摘要：{self.event_summary}
当前情绪：{self.current_sentiment}
预测天数：{self.time_range}天

模拟数据概况：
- 总动作数：{len(self.simulation_data.get('all_actions', []))}
- Agent数量：{self.simulation_data.get('agent_count', 0)}

请输出预测策略JSON。"""

        messages = [
            {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.llm.chat(messages, temperature=0.5, max_tokens=1000)

            if response is None:
                return self._get_default_plan()

            content = response if isinstance(response, str) else response.get("content", "")

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            plan = json.loads(content.strip())

            self.prediction_logger.log_planning_thought(
                f"事件类型: {plan.get('event_type', 'general')}, "
                f"分析工具: {[p['tool'] for p in plan.get('analysis_plan', [])]}"
            )
            self.prediction_logger.log_planning_complete(plan)

            return plan

        except Exception as e:
            logger.warning(f"Planning failed, using default plan: {e}")
            return self._get_default_plan()

    def _get_default_plan(self) -> Dict[str, Any]:
        """获取默认分析计划"""
        return {
            "event_type": "general",
            "event_features": ["舆情事件"],
            "analysis_plan": [
                {"tool": "sir_model_analyzer", "reason": "分析传播趋势", "priority": 1},
                {"tool": "bayesian_predictor", "reason": "预测情景概率", "priority": 2},
                {"tool": "risk_assessor", "reason": "评估风险节点", "priority": 3},
            ],
            "key_questions": ["舆情将如何发展？", "存在哪些风险？"],
            "risk_focus": ["热度变化", "情绪转折"],
        }

    def _execute_analysis(
        self, progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """执行分析 - 按计划调用工具"""
        results = {}

        tools_priority = {
            "sir_model_analyzer": 1,
            "bayesian_predictor": 2,
            "sentiment_analyzer": 3,
            "risk_assessor": 4,
            "intervention_simulator": 5,
        }

        sorted_plan = sorted(
            self.analysis_plan,
            key=lambda x: tools_priority.get(x.get("tool", ""), 99)
        )

        total_modules = len(sorted_plan)
        for i, module in enumerate(sorted_plan):
            tool_name = module.get("tool", "")
            if not tool_name:
                continue

            base_progress = 20 + int((i / max(total_modules, 1)) * 60)

            if progress_callback:
                progress_callback(
                    "analyzing",
                    base_progress,
                    f"正在分析: {tool_name}..."
                )

            self.prediction_logger.log_module_start(tool_name, i)

            # 直接执行工具
            result = self._execute_tool(tool_name, {})
            results[tool_name] = result
            self.analysis_results[tool_name] = result

            self.prediction_logger.log_module_complete(tool_name, i, result)

        return self._integrate_results(results)

    def _analyze_with_react(
        self,
        tool_name: str,
        module_index: int,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """使用ReACT模式分析单个模块"""

        context_prompt = f"""当前分析任务：{tool_name}

事件摘要：{self.event_summary}
当前情绪：{self.current_sentiment}
预测天数：{self.time_range}天

已有分析结果：
{json.dumps(self.analysis_results, ensure_ascii=False, indent=2) if self.analysis_results else '暂无'}

请使用ReACT模式进行分析。"""

        messages = [
            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": context_prompt},
        ]

        tool_calls_count = 0
        max_iterations = 5
        used_tools = set()
        all_tools = {
            "sir_model_analyzer",
            "bayesian_predictor",
            "sentiment_analyzer",
            "risk_assessor",
            "intervention_simulator",
        }

        for iteration in range(max_iterations):
            response = self.llm.chat(messages, temperature=0.5, max_tokens=2000)

            if response is None:
                if iteration < max_iterations - 1:
                    messages.append({"role": "assistant", "content": "（响应为空）"})
                    messages.append({"role": "user", "content": "请继续分析。"})
                    continue
                break

            tool_calls = self._parse_tool_calls(response)
            has_tool_calls = bool(tool_calls)
            has_final_answer = "Final Answer:" in response

            self.prediction_logger.log_llm_response(
                module_name=tool_name,
                module_index=module_index,
                response=response,
                iteration=iteration + 1,
                has_tool_calls=has_tool_calls,
                has_final_answer=has_final_answer,
            )

            if has_final_answer:
                if tool_calls_count < self.MIN_TOOL_CALLS_PER_MODULE:
                    messages.append({"role": "assistant", "content": response})
                    unused_tools = all_tools - used_tools
                    unused_hint = (
                        f"（这些工具还未使用: {', '.join(unused_tools)}）"
                        if unused_tools else ""
                    )
                    messages.append({
                        "role": "user",
                        "content": REACT_INSUFFICIENT_TOOLS_MSG.format(
                            tool_calls_count=tool_calls_count,
                            min_tool_calls=self.MIN_TOOL_CALLS_PER_MODULE,
                            unused_hint=unused_hint,
                        ),
                    })
                    continue

                final_answer = response.split("Final Answer:")[-1].strip()
                return {"result": final_answer, "tool_calls_count": tool_calls_count}

            if has_tool_calls:
                if tool_calls_count >= self.MAX_TOOL_CALLS_PER_MODULE:
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": REACT_TOOL_LIMIT_MSG.format(
                            max_tool_calls=self.MAX_TOOL_CALLS_PER_MODULE,
                        ),
                    })
                    continue

                call = tool_calls[0]

                self.prediction_logger.log_tool_call(
                    module_name=tool_name,
                    module_index=module_index,
                    tool_name=call["name"],
                    parameters=call.get("parameters", {}),
                    iteration=iteration + 1,
                )

                result = self._execute_tool(call["name"], call.get("parameters", {}))

                self.prediction_logger.log_tool_result(
                    module_name=tool_name,
                    module_index=module_index,
                    tool_name=call["name"],
                    result=result,
                    iteration=iteration + 1,
                )

                tool_calls_count += 1
                used_tools.add(call["name"])

                self.analysis_results[call["name"]] = result

                unused_tools = all_tools - used_tools
                unused_hint = ""
                if unused_tools and tool_calls_count < self.MAX_TOOL_CALLS_PER_MODULE:
                    unused_hint = REACT_UNUSED_TOOLS_HINT.format(
                        unused_list="、".join(unused_tools)
                    )

                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": REACT_OBSERVATION_TEMPLATE.format(
                        tool_name=call["name"],
                        result=json.dumps(result, ensure_ascii=False)[:1500],
                        tool_calls_count=tool_calls_count,
                        max_tool_calls=self.MAX_TOOL_CALLS_PER_MODULE,
                        used_tools_str=", ".join(used_tools),
                        unused_hint=unused_hint,
                    ),
                })
                continue

            messages.append({"role": "assistant", "content": response})

            if tool_calls_count < self.MIN_TOOL_CALLS_PER_MODULE:
                unused_tools = all_tools - used_tools
                unused_hint = (
                    f"（这些工具还未使用: {', '.join(unused_tools)}）"
                    if unused_tools else ""
                )
                messages.append({
                    "role": "user",
                    "content": f"请继续调用工具进行分析。{unused_hint}",
                })
                continue

            return {"result": response, "tool_calls_count": tool_calls_count}

        return {"result": "分析超时", "tool_calls_count": tool_calls_count}

    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """解析工具调用"""
        pattern = r'<tool_call\s+name="([^"]+)">\s*(.*?)\s*</tool_callcall>'
        matches = re.findall(pattern, response, re.DOTALL)

        tool_calls = []
        for name, params_str in matches:
            try:
                params = json.loads(params_str.strip()) if params_str.strip() else {}
            except json.JSONDecodeError:
                params = {}

            tool_calls.append({"name": name, "parameters": params})

        return tool_calls

    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """执行工具调用"""
        if tool_name == "sir_model_analyzer":
            return self._tool_sir_model(parameters)
        elif tool_name == "bayesian_predictor":
            return self._tool_bayesian_predictor(parameters)
        elif tool_name == "sentiment_analyzer":
            return self._tool_sentiment_analyzer(parameters)
        elif tool_name == "risk_assessor":
            return self._tool_risk_assessor(parameters)
        elif tool_name == "intervention_simulator":
            return self._tool_intervention_simulator(parameters)
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def _tool_sir_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """SIR传播模型分析"""
        event_summary = params.get("event_summary", self.event_summary)
        sentiment = params.get("current_sentiment", self.current_sentiment)
        days = params.get("days", self.time_range)

        try:
            timeline = self.algorithm_engine.generate_timeline(
                event_summary=event_summary,
                current_sentiment=sentiment,
                days=days
            )

            peak_day = max(timeline, key=lambda x: x.get("heat", 0))
            peak_heat = peak_day.get("heat", 0)

            return {
                "timeline": timeline,
                "peak_day": peak_day.get("day", 1),
                "peak_heat": peak_heat,
                "trend": "上升" if timeline[0].get("heat", 0) < peak_heat else "下降",
                "summary": f"热度将在第{peak_day.get('day', 1)}天达到峰值{peak_heat}，整体趋势{'上升后下降' if peak_day.get('day', 1) > 1 else '持续下降'}",
            }
        except Exception as e:
            return {"error": str(e), "timeline": []}

    def _tool_bayesian_predictor(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """贝叶斯情景预测"""
        event_summary = params.get("event_summary", self.event_summary)
        sentiment = params.get("current_sentiment", self.current_sentiment)

        try:
            scenarios = self.algorithm_engine.generate_scenarios(
                event_summary=event_summary,
                current_sentiment=sentiment
            )

            top_scenario = scenarios[0] if scenarios else {}
            high_risk_count = sum(1 for s in scenarios if s.get("risk_level") == "high")

            return {
                "scenarios": scenarios,
                "top_scenario": top_scenario.get("name", ""),
                "top_probability": top_scenario.get("probability", 0),
                "high_risk_count": high_risk_count,
                "summary": f"最可能情景「{top_scenario.get('name', '')}」概率{top_scenario.get('probability', 0)}%，存在{high_risk_count}个高风险情景",
            }
        except Exception as e:
            return {"error": str(e), "scenarios": []}

    def _tool_sentiment_analyzer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """情绪趋势分析"""
        event_summary = params.get("event_summary", self.event_summary)
        timeline = params.get("timeline", [])

        if not timeline:
            timeline = self.analysis_results.get("sir_model_analyzer", {}).get("timeline", [])

        if not timeline:
            return {"error": "No timeline data available"}

        sentiments = [t.get("sentiment", 0.5) for t in timeline]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.5

        trend = "稳定"
        if len(sentiments) >= 2:
            if sentiments[-1] > sentiments[0] + 0.1:
                trend = "向好"
            elif sentiments[-1] < sentiments[0] - 0.1:
                trend = "恶化"

        turning_points = []
        for i in range(1, len(sentiments)):
            if abs(sentiments[i] - sentiments[i-1]) > 0.15:
                turning_points.append({
                    "day": i + 1,
                    "change": sentiments[i] - sentiments[i-1],
                    "direction": "正面" if sentiments[i] > sentiments[i-1] else "负面"
                })

        return {
            "average_sentiment": round(avg_sentiment, 2),
            "trend": trend,
            "turning_points": turning_points[:3],
            "summary": f"平均情绪指数{round(avg_sentiment, 2)}，整体趋势{trend}，发现{len(turning_points)}个情绪转折点",
        }

    def _tool_risk_assessor(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """风险节点评估"""
        timeline = params.get("timeline", [])
        scenarios = params.get("scenarios", [])

        if not timeline:
            timeline = self.analysis_results.get("sir_model_analyzer", {}).get("timeline", [])
        if not scenarios:
            scenarios = self.analysis_results.get("bayesian_predictor", {}).get("scenarios", [])

        warnings = []

        for node in timeline:
            if node.get("risk") == "high":
                warnings.append({
                    "day": node.get("day"),
                    "type": "热度风险",
                    "level": "high",
                    "description": node.get("event", ""),
                    "suggestion": "建议提前准备应对方案",
                })

        high_risk_scenarios = [s for s in scenarios if s.get("risk_level") == "high"]
        for scenario in high_risk_scenarios[:2]:
            warnings.append({
                "day": 0,
                "type": "情景风险",
                "level": "high",
                "description": f"可能出现：{scenario.get('name')}",
                "suggestion": f"关注因素：{', '.join(scenario.get('key_factors', [])[:2])}",
            })

        risk_summary = {
            "high": sum(1 for w in warnings if w.get("level") == "high"),
            "medium": sum(1 for w in warnings if w.get("level") == "medium"),
            "low": sum(1 for w in warnings if w.get("level") == "low"),
        }

        return {
            "warnings": warnings[:5],
            "risk_distribution": risk_summary,
            "summary": f"识别出{len(warnings)}个风险节点，其中高风险{risk_summary['high']}个",
        }

    def _tool_intervention_simulator(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """干预策略模拟"""
        event_summary = params.get("event_summary", self.event_summary)
        intervention = params.get("intervention", "官方回应")
        sentiment = params.get("current_sentiment", self.current_sentiment)

        prompt = f"""分析以下干预策略对舆情的影响：

事件：{event_summary}
干预措施：{intervention}
当前情绪：{sentiment}

请输出JSON格式：
{{
    "heat_change": -15,
    "sentiment_change": 0.2,
    "effectiveness": "高/中/低",
    "risks": ["风险1"],
    "recommendation": 4,
    "analysis": "效果分析"
}}"""

        try:
            response = self.llm.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )

            content = response if isinstance(response, str) else response.get("content", "")

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
            return result

        except Exception as e:
            return {
                "heat_change": -10,
                "sentiment_change": 0.1,
                "effectiveness": "中",
                "risks": ["效果不确定"],
                "recommendation": 3,
                "analysis": f"模拟失败: {str(e)}",
            }

    def _integrate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """整合分析结果"""
        timeline = results.get("sir_model_analyzer", {}).get("timeline", [])
        scenarios = results.get("bayesian_predictor", {}).get("scenarios", [])
        warnings = results.get("risk_assessor", {}).get("warnings", [])

        scenario_summary = ""
        if scenarios:
            top = scenarios[0]
            high_risk = sum(1 for s in scenarios if s.get("risk_level") == "high")
            scenario_summary = f"最可能情景「{top.get('name', '')}」概率{top.get('probability', 0)}%，存在{high_risk}个高风险情景"

        visualization = self._generate_visualization(timeline, scenarios, warnings)

        return {
            "timeline": timeline,
            "scenarios": scenarios,
            "scenario_summary": scenario_summary,
            "warnings": warnings,
            "visualization": visualization,
        }

    def _generate_visualization(
        self, timeline: List[Dict], scenarios: List[Dict], warnings: List[Dict]
    ) -> Dict[str, Any]:
        """生成可视化数据"""
        heat_curve = [{"day": n["day"], "value": n["heat"]} for n in timeline] if timeline else []
        sentiment_curve = [{"day": n["day"], "value": n["sentiment"]} for n in timeline] if timeline else []

        probability_data = [
            {"name": s["name"], "value": s["probability"], "risk": s.get("risk_level", "medium")}
            for s in scenarios
        ] if scenarios else []

        risk_count = {"high": 0, "medium": 0, "low": 0}
        for s in scenarios:
            risk = s.get("risk_level", "medium")
            risk_count[risk] = risk_count.get(risk, 0) + 1

        return {
            "heat_curve": heat_curve,
            "sentiment_curve": sentiment_curve,
            "probability_chart": probability_data,
            "risk_distribution": risk_count,
        }

    def _reflect_and_conclude(
        self,
        results: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """反思并生成最终结论"""
        self.prediction_logger.log_reflection_start()

        context_prompt = f"""请对以下预测结果进行反思和总结：

事件摘要：{self.event_summary}
当前情绪：{self.current_sentiment}

预测结果：
{json.dumps(results, ensure_ascii=False, indent=2)[:3000]}

请输出反思结果JSON。"""

        messages = [
            {"role": "system", "content": REFLECTION_SYSTEM_PROMPT},
            {"role": "user", "content": context_prompt},
        ]

        try:
            response = self.llm.chat(messages, temperature=0.5, max_tokens=800)

            if response is None:
                return self._get_default_conclusion(results)

            content = response if isinstance(response, str) else response.get("content", "")

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            conclusion = json.loads(content.strip())

            self.prediction_logger.log_reflection_result(
                conclusion.get("final_conclusion", ""),
                conclusion.get("confidence", 0.8)
            )

            return conclusion

        except Exception as e:
            logger.warning(f"Reflection failed: {e}")
            return self._get_default_conclusion(results)

    def _get_default_conclusion(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """获取默认结论"""
        scenarios = results.get("scenarios", [])
        top = scenarios[0] if scenarios else {}

        return {
            "confidence": 0.75,
            "consistency_check": "各模块结果基本一致",
            "key_insights": ["舆情发展存在不确定性", "需关注关键风险节点"],
            "action_suggestions": ["持续监测舆情动态", "准备应急预案"],
            "final_conclusion": f"基于预测分析，「{top.get('name', '未知')}」是最可能出现的情景，建议持续关注舆情发展。",
        }

    def _generate_fallback_result(self) -> Dict[str, Any]:
        """生成降级结果"""
        return {
            "prediction_id": f"pred_{int(time.time() * 1000)}",
            "simulation_id": self.simulation_id,
            "event_summary": self.event_summary,
            "current_sentiment": self.current_sentiment,
            "time_range": self.time_range,
            "generated_at": datetime.now().isoformat(),
            "timeline": [],
            "scenarios": [],
            "scenario_summary": "预测失败，请重试",
            "warnings": [],
            "visualization": {},
            "conclusion": "预测分析失败，请检查输入数据后重试。",
            "confidence": 0.5,
            "key_insights": [],
            "action_suggestions": ["请重新执行预测"],
            "error": True,
        }


def create_prediction_agent(
    simulation_id: str = None,
    event_summary: str = "",
    current_sentiment: str = "中性",
    time_range: int = 7,
    simulation_data: Dict[str, Any] = None,
) -> PredictionAgent:
    """创建预测Agent实例"""
    return PredictionAgent(
        simulation_id=simulation_id,
        event_summary=event_summary,
        current_sentiment=current_sentiment,
        time_range=time_range,
        simulation_data=simulation_data,
    )
