from survey_database import SurveyDatabase

# Initialize database
db = SurveyDatabase("survey_data.json")

# Show statistics
stats = db.get_statistics()
print(f"\nTotal questions: {stats['total_questions']}")
print(f"Categories: {stats['categories_distribution']}")