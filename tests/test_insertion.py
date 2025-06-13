# import asyncio
# import sys
# from pathlib import Path

# # Add project root to Python path
# project_root = Path(__file__).parent
# sys.path.insert(0, str(project_root))

# from dotenv import load_dotenv
# load_dotenv()

# # Sample data from your original post
# google_sample_data = [
#     {
#         "reviewId": "f5481bbc-347d-4f3e-ab23-24c7d377a8ba",
#         "userName": "KAZEVER STEPHEN",
#         "userImage": "https://play-lh.googleusercontent.com/a-/ALV-UjWU6D5k_uLO09UXiqxXogooOaRCpp8CzjGsG6dHob3AsZgAh_p-",
#         "content": "yeah",
#         "score": 5,
#         "thumbsUpCount": 0,
#         "reviewCreatedVersion": "25.03.10.0",
#         "at": "2025-05-31T08:40:23Z",
#         "replyContent": None,
#         "repliedAt": None,
#         "appVersion": "25.03.10.0"
#     },
#     {
#         "reviewId": "59a0153c-cb90-415e-a8a2-67222ceddb50",
#         "userName": "Dan Vrátil",
#         "userImage": "https://play-lh.googleusercontent.com/a-/ALV-UjVZDwuasMid5NfIcIobm8yVezAyJVEaXrW1VcsoEIoAZJICZ2qi",
#         "content": "I don't have to use Teams: 5 stars",
#         "score": 5,
#         "thumbsUpCount": 0,
#         "reviewCreatedVersion": "23.07.10.0",
#         "at": "2025-05-29T12:24:24Z",
#         "replyContent": None,
#         "repliedAt": None,
#         "appVersion": "23.07.10.0"
#     }
# ]

# apple_sample_data = [
#     {
#         "id": 12716066970,
#         "date": "2025-05-30T09:13:34-07:00",
#         "user_name": "Malyuggd",
#         "title": "Good but it tuck ages to downlowd",
#         "content": "Good but it tuck ages to downlowd",
#         "rating": 1,
#         "app_version": "1.21.81"
#     },
#     {
#         "id": 12715964619,
#         "date": "2025-05-30T08:43:25-07:00",
#         "user_name": "Mr. I LOVE YOUR GAMES",
#         "title": ".Cool but one annoying thing",
#         "content": "I don't know why but every time I use vibrant visuals the sky go's black.",
#         "rating": 5,
#         "app_version": "1.21.81"
#     }
# ]

# async def test_insertion():
#     """Test data insertion with sample data"""
#     try:
#         # Import your database connection and service
#         from backend.database import connection as db_connection
#         from backend.services.review_insertion_service import ReviewInsertionService
        
#         # Initialize database connection
#         print("🔹 Connecting to database...")
#         await db_connection.connect_to_db()
#         await db_connection.test_connection()
        
#         service = ReviewInsertionService()
        
#         print("🧪 Testing Google Reviews insertion...")
#         google_result = await service.insert_google_reviews(
#             reviews=google_sample_data, 
#             app_id="com.slack"
#         )
#         print(f"Google Result: {google_result}")
        
#         print("\n🧪 Testing Apple Reviews insertion...")
#         apple_result = await service.insert_apple_reviews(
#             reviews=apple_sample_data, 
#             app_id="com.slack"
#         )
#         print(f"Apple Result: {apple_result}")
        
#         print("\n📊 Getting review stats...")
#         stats = await service.get_review_stats("com.slack")
#         print(f"Stats: {stats}")
        
#         print("\n✅ Test completed successfully!")
        
#     except ImportError as e:
#         print(f"❌ Could not import service: {e}")
#         print("Please create the ReviewInsertionService first!")
#     except Exception as e:
#         print(f"❌ Test failed: {e}")
#         import traceback
#         traceback.print_exc()
#     finally:
#         # Close database connection
#         try:
#             await db_connection.close_db_connection()
#         except:
#             pass

# if __name__ == "__main__":
#     asyncio.run(test_insertion())