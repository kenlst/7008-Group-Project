from survey_database import SurveyDatabase

def test_database_functionality():
    """Test database functionality"""
    print("=== Survey System Database Test ===\n")
    
    # Initialize database
    db = SurveyDatabase("survey_data.json")
    
    # 1. Test get all questions
    print("1. All Questions:")
    questions = db.get_all_questions()
    for q in questions:
        print(f"   ID: {q['id']}, Question: {q['question_text']}, Category: {q['category']}")
    
    # 2. Test get question by ID
    print("\n2. Get Question by ID:")
    question = db.get_question_by_id(1)
    if question:
        print(f"   Question 1: {question['question_text']}")
    
    # 3. Test get questions by category
    print("\n3. Questions in Satisfaction Category:")
    satisfaction_questions = db.get_questions_by_category("Satisfaction")
    for q in satisfaction_questions:
        print(f"   - {q['question_text']}")
    
    # 4. Test get all questionnaires
    print("\n4. All Questionnaires:")
    questionnaires = db.get_all_questionnaires()
    for qn in questionnaires:
        print(f"   Questionnaire: {qn['title']}, Status: {qn['status']}")
    
    # 5. Test data statistics
    print("\n5. Data Statistics:")
    stats = db.get_statistics()
    print(f"   Total Questions: {stats['total_questions']}")
    print(f"   Total Questionnaires: {stats['total_questionnaires']}")
    print(f"   Total Users: {stats['total_users']}")
    print(f"   Categories Distribution: {stats['categories_distribution']}")
    print(f"   Question Types Distribution: {stats['question_types_distribution']}")
    
    # 6. Test add new question
    print("\n6. Test Add New Question:")
    new_question = {
        "question_text": "Do you think our product price is reasonable?",
        "question_type": "single_choice",
        "options": ["Very reasonable", "Reasonable", "Neutral", "Unreasonable"],
        "difficulty": 2.0,
        "category": "Price",
        "tags": ["price", "value", "reasonableness"]
    }
    new_id = db.add_question(new_question)
    print(f"   New question added successfully, ID: {new_id}")
    
    # 7. Test create new questionnaire
    print("\n7. Test Create New Questionnaire:")
    requirements = {
        "question_count": 3,
        "categories": ["Price", "Satisfaction"],
        "difficulty_range": [1.0, 2.5]
    }
    new_qn_id = db.create_questionnaire(
        title="Price Satisfaction Survey",
        description="Understand user opinions on product pricing",
        target_audience="All Users",
        requirements=requirements
    )
    print(f"   New questionnaire created successfully, ID: {new_qn_id}")
    
    # 8. Test add question to questionnaire
    print("\n8. Test Add Question to Questionnaire:")
    success = db.add_question_to_questionnaire(new_qn_id, new_id)
    print(f"   Add question to questionnaire: {'Success' if success else 'Failed'}")
    
    # 9. Verify final data
    print("\n9. Final Data Verification:")
    final_stats = db.get_statistics()
    print(f"   Final Questions Count: {final_stats['total_questions']}")
    print(f"   Final Questionnaires Count: {final_stats['total_questionnaires']}")

if __name__ == "__main__":
    test_database_functionality()