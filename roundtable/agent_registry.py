from collections import Counter


class AgentRegistry:
    def __init__(self, agents: list):
        self.agents = agents

    def list_all(self) -> list:
        """返回所有专家列表"""
        return list(self.agents)

    def list_by_category(self, category: str) -> list:
        """返回指定分类的专家列表，category 不区分大小写"""
        key = category.casefold()
        return [a for a in self.agents if a.category.casefold() == key]

    def get_by_id(self, agent_id: str):
        """根据 id 返回专家，找不到返回 None"""
        for agent in self.agents:
            if agent.id == agent_id:
                return agent
        return None

    def search(self, keyword: str) -> list:
        """在 name、category、description 中搜索关键词，不区分大小写，返回匹配列表"""
        if not keyword:
            return []
        key = keyword.casefold()
        results = []
        for agent in self.agents:
            haystack = " ".join((agent.name, agent.category, agent.description)).casefold()
            if key in haystack:
                results.append(agent)
        return results

    def list_categories(self) -> list:
        """返回所有分类名称（去重、排序）"""
        return sorted({a.category for a in self.agents})

    def summary(self) -> str:
        """返回一段文字，格式为：共加载 X 位专家，分布在 Y 个分类：category1(N位), category2(N位)..."""
        total = len(self.agents)
        counts = Counter(a.category for a in self.agents)
        parts = [f"{cat}({counts[cat]}位)" for cat in sorted(counts)]
        categories_text = ", ".join(parts)
        return f"共加载 {total} 位专家，分布在 {len(counts)} 个分类：{categories_text}"


if __name__ == "__main__":
    from roundtable.agent_loader import load_expert_agents

    agents = load_expert_agents()
    registry = AgentRegistry(agents)

    print(registry.summary())
    print()
    for agent in registry.list_all()[:3]:
        print(f"- {agent.name} ({agent.category})")
