"""
标题优化器 - 自动生成和评分爆款标题
"""
import random
from typing import List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TitleOptimizer:
    """标题优化器"""
    
    def __init__(self, templates_path: str = None):
        """
        初始化标题优化器
        
        Args:
            templates_path: 标题模板文件路径
        """
        self.templates = self._get_default_templates()
    
    def _get_default_templates(self) -> Dict[str, Any]:
        """获取默认标题模板"""
        return {
            "ai_tools": {
                "templates": [
                    "这{number}款AI工具，让我效率提升{percentage}%（附下载）",
                    "我用AI{action}，{result}（附资源）",
                    "{year}年必备！{number}个AI工具推荐",
                    "普通人也能{action}！AI让{benefit}",
                    "【推荐】{number}款免费AI工具，{benefit}",
                    "{audience}必备！这{number}款AI工具让{benefit}",
                    "AI工具实测：{number}款提升效率神器",
                    "效率提升{percentage}%！我的AI工具清单",
                    "从{start}到{end}，AI工具完整指南",
                    "这{number}个AI技巧，让我{result}"
                ]
            },
            "side_hustle": {
                "templates": [
                    "副业月入{amount}，我是如何{method}的",
                    "{time}开始副业，{result}（附资源）",
                    "从{start}到{end}，我的副业{journey}",
                    "{number}个适合{audience}的副业方向",
                    "普通人副业{action}，{benefit}实战分享",
                    "副业避坑指南：{number}个{mistake}",
                    "我用副业{time}赚了{amount}",
                    "副业{action}，{number}个步骤（详细教程）"
                ]
            },
            "efficiency": {
                "templates": [
                    "这{number}个工具，让{benefit}",
                    "效率提升{percentage}%！我的{number}个方法",
                    "{tool}使用指南，效率提升{percentage}%",
                    "从{start}到{end}，{tool}完整教程",
                    "{number}分钟学会{skill}，{benefit}",
                    "效率神器推荐：{number}款{category}工具",
                    "如何{action}？{number}个方法（附案例）"
                ]
            },
            "tech_trends": {
                "templates": [
                    "{year}年{number}大科技趋势，{benefit}",
                    "即将{action}！这{number}个变化必须知道",
                    "未来{time}，{field}将{change}",
                    "深度解读：{topic}，{benefit}",
                    "为什么{topic}很重要？{number}个理由",
                    "一文看懂{topic}，{benefit}"
                ]
            }
        }
    
    def score_title(self, title: str) -> Dict[str, Any]:
        """
        评分标题
        
        Args:
            title: 标题文本
        
        Returns:
            {
                'score': 总分,
                'details': {
                    'curiosity_gap': 好奇缺口分数,
                    'value_promise': 价值承诺分数,
                    'identity': 身份认同分数,
                    'numbers_symbols': 数字符号分数,
                    'length': 长度分数
                }
            }
        """
        details = {
            'curiosity_gap': self._score_curiosity_gap(title),
            'value_promise': self._score_value_promise(title),
            'identity': self._score_identity(title),
            'numbers_symbols': self._score_numbers_symbols(title),
            'length': self._score_length(title)
        }
        
        total_score = sum(details.values())
        
        return {
            'score': total_score,
            'details': details
        }
    
    def _score_curiosity_gap(self, title: str) -> int:
        """评分好奇心缺口（30分）"""
        score = 0
        
        # 好奇词
        curiosity_words = ['这', '那个', '没想到', '原来', '竟然', '居然', '为什么', '如何', '什么']
        for word in curiosity_words:
            if word in title:
                score += 10
                break
        
        # 疑问句
        if '？' in title or '?' in title:
            score += 10
        
        # 悬念词
        suspense_words = ['最后', '结果', '真相', '秘密', '惊人']
        for word in suspense_words:
            if word in title:
                score += 10
                break
        
        return min(score, 30)
    
    def _score_value_promise(self, title: str) -> int:
        """评分价值承诺（25分）"""
        score = 0
        
        # 数字承诺
        if any(char.isdigit() for char in title):
            score += 10
        
        # 价值词
        value_words = ['提升', '提高', '增加', '减少', '节省', '学会', '掌握', '获得', '领取', '下载']
        for word in value_words:
            if word in title:
                score += 10
                break
        
        # 结果词
        result_words = ['附', '完整', '详细', '教程', '指南', '清单', '资源']
        for word in result_words:
            if word in title:
                score += 5
                break
        
        return min(score, 25)
    
    def _score_identity(self, title: str) -> int:
        """评分身份认同（20分）"""
        score = 0
        
        # 身份词
        identity_words = ['普通人', '程序员', '打工人', '学生', '创业者', '家长', '职场人', '小白', '新手']
        for word in identity_words:
            if word in title:
                score += 20
                break
        
        return min(score, 20)
    
    def _score_numbers_symbols(self, title: str) -> int:
        """评分数字符号（15分）"""
        score = 0
        
        # 数字
        if any(char.isdigit() for char in title):
            score += 10
        
        # 符号
        symbols = ['【', '】', '！', '？', '🔥', '⭐', '✅', '💡']
        for symbol in symbols:
            if symbol in title:
                score += 5
                break
        
        return min(score, 15)
    
    def _score_length(self, title: str) -> int:
        """评分长度（10分）"""
        length = len(title)
        
        if 20 <= length <= 35:
            return 10
        elif 15 <= length <= 40:
            return 5
        else:
            return 0
    
    def generate_titles(self, topic: str, category: str = "ai_tools", count: int = 5) -> List[Dict[str, Any]]:
        """
        生成多个候选标题
        
        Args:
            topic: 主题
            category: 分类（ai_tools/side_hustle/efficiency/tech_trends）
            count: 生成数量
        
        Returns:
            [{'title': 标题, 'score': 分数, 'details': 详情}]
        """
        templates = self.templates.get(category, {}).get('templates', [])
        
        if not templates:
            return []
        
        results = []
        
        # 随机选择模板
        selected_templates = random.sample(templates, min(count, len(templates)))
        
        for template in selected_templates:
            # 替换变量
            title = self._fill_template(template, topic)
            
            # 评分
            score_result = self.score_title(title)
            
            results.append({
                'title': title,
                'score': score_result['score'],
                'details': score_result['details']
            })
        
        # 按分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
    
    def _fill_template(self, template: str, topic: str) -> str:
        """填充模板变量"""
        replacements = {
            '{number}': str(random.randint(3, 10)),
            '{benefit}': '效率大幅提升',
            '{resource}': '完整教程',
            '{action}': '提升效率',
            '{result}': '效果显著',
            '{skill}': topic,
            '{year}': '2026',
            '{category}': 'AI',
            '{audience}': '普通人',
            '{percentage}': str(random.randint(100, 500)),
            '{amount}': '过万',
            '{method}': '这样做',
            '{time}': '3个月',
            '{start}': '零基础',
            '{end}': '月入过万',
            '{journey}': '进阶之路',
            '{experience}': '经验分享',
            '{mistake}': '常见错误',
            '{tool}': 'AI工具',
            '{case_study}': '实战案例',
            '{field}': 'AI领域',
            '{change}': '重大变化',
            '{topic}': topic,
            '{opinion}': '我的思考',
            '{advantage}': '优势',
            '{disadvantage}': '挑战'
        }
        
        result = template
        for key, value in replacements.items():
            result = result.replace(key, value)
        
        return result
    
    def select_best_title(self, titles: List[Dict[str, Any]]) -> str:
        """
        选择最佳标题
        
        Args:
            titles: 候选标题列表
        
        Returns:
            最佳标题
        """
        if not titles:
            return ""
        
        return titles[0]['title']


def optimize_title(topic: str, category: str = "ai_tools") -> str:
    """
    优化标题（便捷函数）
    
    Args:
        topic: 主题
        category: 分类
    
    Returns:
        最佳标题
    """
    optimizer = TitleOptimizer()
    titles = optimizer.generate_titles(topic, category, count=5)
    
    if titles:
        logger.info(f"📊 生成 {len(titles)} 个候选标题:")
        for i, t in enumerate(titles, 1):
            logger.info(f"  {i}. {t['title']} (分数: {t['score']})")
        
        return optimizer.select_best_title(titles)
    
    return topic


if __name__ == "__main__":
    # 测试
    optimizer = TitleOptimizer()
    
    # 生成标题
    titles = optimizer.generate_titles("AI工具", "ai_tools", count=5)
    
    print("\n📊 生成的标题:")
    for i, t in enumerate(titles, 1):
        print(f"{i}. {t['title']}")
        print(f"   总分: {t['score']}")
        print(f"   详情: {t['details']}")
        print()
    
    # 选择最佳
    best = optimizer.select_best_title(titles)
    print(f"✅ 最佳标题: {best}")
