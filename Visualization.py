import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List
import os


class DataVisualization:
    """
    Data Visualization Class
    Main function: Generate various charts to display system status and analysis results
    """

    def __init__(self):
        self.chart_templates = {}  # Chart template configuration

    def create_cluster_visualization(self, cluster_data: Dict[str, Any]) -> str:
        """
        Create cluster result visualization chart
        Display: Distribution of questions in 2D space, different clusters in different colors
        """
        # TODO: Use matplotlib/seaborn to create scatter plot
        # Display distribution of each cluster and cluster centers

        return "cluster_visualization.png"  # Return chart file path

    def create_category_distribution_chart(self, category_data: Dict[str, int]) -> str:
        """
        Create question category distribution chart
        Display: Number distribution of questions across travel question categories
        """
        # TODO: Create bar chart or pie chart
        # Display number of questions in accommodation, transportation, food, etc. categories

        filtered_data = {k: v for k, v in category_data.items() if k.lower() != "general"}

        categories = list(filtered_data.keys())
        counts = list(filtered_data.values())

        plt.figure(figsize=(8, 6))
        sns.set(style="whitegrid")
        sns.barplot(x=categories, y=counts, hue=categories, palette="pastel", legend=False)

        plt.title("Question Category Distribution (Excluding 'General')", fontsize=14)
        plt.xlabel("Category")
        plt.ylabel("Number of Questions")
        plt.xticks(rotation=30)

        output_path = "category_distribution.png"
        plt.savefig(output_path, dpi=150)
        plt.close()

        return output_path
        # return "category_distribution.png"

    def create_complexity_analysis_chart(self, complexity_data: Dict[str, int]) -> str:
        """
        Create complexity analysis chart
        Display: Proportion distribution of easy, medium, hard questions
        """
        # TODO: Create stacked bar chart or donut chart

        difficulties = []
        for diff_str, count in complexity_data.items():
            diff = float(diff_str)  # 字典 key 是 str，需要转 float
            difficulties.extend([diff] * count)

        if len(difficulties) == 0:
            print("Warning: No difficulty data to plot.")
            return ""

        plt.figure(figsize=(8, 5))
        sns.set(style="whitegrid")

        # 直方图 + KDE 曲线
        sns.histplot(
            difficulties,
            bins=6,
            kde=True,
            color="skyblue",
            edgecolor="black"
        )

        plt.title("Difficulty Distribution", fontsize=14)
        plt.xlabel("Difficulty Score")
        plt.ylabel("Number of Questions")

        output_path = "complexity_analysis.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()

        return output_path
        #return "complexity_analysis.png"

    def create_platform_comparison_chart(self, platform_data: Dict[str, int]) -> str:
        """
        Create platform data comparison chart
        Display: Comparison of question quantity and quality across different travel platforms
        """
        # TODO: Create multi-series bar chart
        # Compare data characteristics of Ctrip, Booking.com, etc. platforms
        return "platform_comparison.png"

    def create_survey_progress_dashboard(self, survey_data: Dict[str, Any]) -> str:
        """
        Create survey progress dashboard
        Display: Questionnaire completion status, user participation, etc.
        """
        # TODO: Create comprehensive dashboard
        return "survey_dashboard.html"

    def create_question_relationship_graph(self, relationship_data: List[Dict]) -> str:
        """
        Create question relationship network graph
        Display: Hierarchical relationships and association networks between questions
        """
        # TODO: Use networkx to create network graph
        # Nodes represent questions, edges represent association relationships
        return "question_relationship.png"

    def create_user_analysis_report(self, user_data: Dict[str, Any]) -> str:
        """
        Create personalized analysis report for individual user
        Input: User data, including user profile, answer records, classification results, dimension scores, etc.
        Output: Visualization (such as html)
        """
        # TODO: Report content: User type, classification basis (key answers), feature radar chart (displaying user scores across multiple dimensions), personalized travel recommendations (destinations, activities, budget, etc.) implement detailed analysis (such as html implementation), mainly including overall user behavior analysis, preference insights, and feedback after individual user completes all questions (user type and personalized recommendations)
        return "user_analysis_report.html"

    def create_allusers_analysis_report(self, system_data: Dict[str, Any]) -> str:
        """Generate overall user analysis report
           Total users, classification status, completion rate, etc.
        """
        return "allusers_analysis_report.html"

    def export_all_visualizations(self, system_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Export all visualization charts
        Input: Data from various system modules
        Output: Dictionary of paths to various chart files
        """
        visualizations = {
            'clusters': self.create_cluster_visualization(system_data.get('cluster_data', {})),
            'categories': self.create_category_distribution_chart(system_data.get('category_data', {})),
            'complexity': self.create_complexity_analysis_chart(system_data.get('complexity_data', {})),
            'platforms': self.create_platform_comparison_chart(system_data.get('platform_data', {})),
            'survey_dashboard': self.create_survey_progress_dashboard(system_data.get('survey_data', {})),
            'relationships': self.create_question_relationship_graph(system_data.get('relationship_data', [])),
            'individual_user_report': self.create_user_analysis_report(system_data.get('user_data', {})),
            'all_users_report': self.create_allusers_analysis_report(system_data.get('system_stats', {}))
        }
        return visualizations


import json

with open("convert_data.json", "r") as f:
    data = json.load(f)

questions = data["questions"]

category_count = {}

for q in questions:
    cat = q["category"]
    category_count[cat] = category_count.get(cat, 0) + 1

viz = DataVisualization()
viz.create_category_distribution_chart(category_count)

difficulty_count = {}
for q in questions:
    diff = str(q["difficulty"])       # 转成字符串做 key（如 "2.0"）
    difficulty_count[diff] = difficulty_count.get(diff, 0) + 1

viz = DataVisualization()
viz.create_complexity_analysis_chart(difficulty_count)


