// 按5轮为单位聚合数据
const groupedRoundData = computed(() => {
  // 优先从 step2 的 time_config 计算轮数（必须按照step2来）
  let totalRounds = 15 // 默认15轮
  const timeConfig = props.simulationConfig?.time_config
  if (timeConfig?.total_simulation_hours && timeConfig?.minutes_per_round) {
    totalRounds = Math.floor((timeConfig.total_simulation_hours * 60) / timeConfig.minutes_per_round)
  }
  // 确保至少15轮
  totalRounds = Math.max(15, totalRounds)
  
  if (simulationRunData.value?.all_actions?.length) {
    const actions = simulationRunData.value.all_actions
    const roundMap = new Map()
    
    // 统计每轮的动作数
    actions.forEach(action => {
      const round = action.round_num || 1
      if (!roundMap.has(round)) {
        roundMap.set(round, { count: 0, actions: [] })
      }
      roundMap.get(round).count++
      roundMap.get(round).actions.push(action)
    })
    
    // 获取所有轮次并排序
    const allRounds = Array.from(roundMap.entries()).sort((a, b) => a[0] - b[0])
    
    // 计算最大动作数用于热度标准化
    const maxCount = Math.max(...allRounds.map(([, d]) => d.count), 1)
    
    // 按5轮分组，显示所有区间（包括无数据的）
    const groups = []
    for (let start = 1; start <= totalRounds; start += 5) {
      const end = Math.min(start + 4, totalRounds)
      const roundsInGroup = allRounds.filter(([r]) => r >= start && r <= end)
      
      const totalActions = roundsInGroup.reduce((sum, [, data]) => sum + data.count, 0)
      
      // 计算热度：有数据则按数据计算，无数据则为0
      let heat = 0
      if (roundsInGroup.length > 0) {
        // 基于该组的动作密度计算热度
        const density = totalActions / (roundsInGroup.length * maxCount)
        heat = Math.min(100, Math.round(density * 100))
      }
      
      let risk = 'low'
      if (heat > 70) risk = 'high'
      else if (heat > 40) risk = 'medium'
      
      groups.push({
        startRound: start,
        endRound: end,
        label: `R${start}-${end}`,
        heat,
        risk,
        actionCount: totalActions,
        roundCount: roundsInGroup.length,
        hasData: roundsInGroup.length > 0
      })
    }
    
    return groups
  } else if (roundHeatData.value.length > 0) {
    // 使用 roundHeatData 作为备用数据
    const groups = []
    
    for (let start = 1; start <= totalRounds; start += 5) {
      const end = Math.min(start + 4, totalRounds)
      const roundsInGroup = roundHeatData.value.filter(r => r.round >= start && r <= end)
      
      if (roundsInGroup.length > 0) {
        const avgHeat = Math.round(roundsInGroup.reduce((sum, r) => sum + r.heat, 0) / roundsInGroup.length)
        let risk = 'low'
        if (avgHeat > 70) risk = 'high'
        else if (avgHeat > 40) risk = 'medium'
        
        groups.push({
          startRound: start,
          endRound: end,
          label: `R${start}-${end}`,
          heat: avgHeat,
          risk,
          actionCount: roundsInGroup.length,
          roundCount: roundsInGroup.length,
          hasData: true
        })
      } else {
        groups.push({
          startRound: start,
          endRound: end,
          label: `R${start}-${end}`,
          heat: 0,
          risk: 'low',
          actionCount: 0,
          roundCount: 0,
          hasData: false
        })
      }
    }
    
    return groups
  }
  
  return []
})