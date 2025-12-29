"""
Test script for Gemini API calls
This script tests various Gemini API functionalities used in the application
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from service.generators.base import GenAIClient, FileUploader
from service.generators.generators import QuestionGenerator, TextProcessor, ImageProcessor, FileProcessor
from service.generators.summarizer import Summarizer
from service.generators.constants import default_prompt


class GeminiAPITester:
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_GENAI_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_GENAI_KEY not found in environment variables")
        
        print(f"✓ API Key loaded: {self.api_key[:10]}...")
        
        # Initialize components
        self.genai_client = GenAIClient(api_key=self.api_key)
        self.file_uploader = FileUploader(api_key=self.api_key)
        self.generator = QuestionGenerator(api_key=self.api_key, default_prompt=default_prompt)
        self.summarizer = Summarizer(api_key=self.api_key)
        self.text_processor = TextProcessor(self.generator)
        self.image_processor = ImageProcessor(self.generator, self.summarizer, self.text_processor)
        self.file_processor = FileProcessor(self.generator)
        
        print("✓ All components initialized successfully\n")

    async def test_simple_text_generation(self):
        """Test 1: Simple text generation with Gemini"""
        print("=" * 60)
        print("TEST 1: Simple Text Generation")
        print("=" * 60)
        
        try:
            prompt = "Explain what is photosynthesis in 2 sentences."
            print(f"Prompt: {prompt}")
            
            response = await self.genai_client.model.generate_content_async(contents=prompt)
            print(f"\nResponse:\n{response.text}\n")
            print("✓ Test 1 PASSED\n")
            return True
        except Exception as e:
            print(f"✗ Test 1 FAILED: {str(e)}\n")
            return False

    async def test_question_generation_from_text(self):
        """Test 2: Generate questions from text"""
        print("=" * 60)
        print("TEST 2: Question Generation from Text")
        print("=" * 60)
        
        try:
            sample_text = """
            Photosynthesis is a process used by plants and other organisms to convert light energy 
            into chemical energy. This chemical energy is stored in carbohydrate molecules, such as 
            sugars and starches, which are synthesized from carbon dioxide and water. Oxygen is 
            released as a byproduct. Most plants, algae, and cyanobacteria perform photosynthesis; 
            such organisms are called photoautotrophs.
            """
            
            print(f"Sample text: {sample_text[:100]}...")
            print(f"Generating 2 questions in English with medium difficulty...\n")
            
            result = await self.text_processor.generate_questions(
                text=sample_text,
                num_question=2,
                language="English",
                difficulty="medium"
            )
            
            print(f"Generated {len(result['questions'])} questions:")
            for i, q in enumerate(result['questions'], 1):
                print(f"\nQuestion {i}:")
                print(f"  Q: {q['question']}")
                print(f"  Options: {q['options']}")
                print(f"  Answer: {q['answer']} - {q['options'][q['answer']]}")
                print(f"  Explanation: {q['explanation']}")
            
            print("\n✓ Test 2 PASSED\n")
            return True
        except Exception as e:
            print(f"✗ Test 2 FAILED: {str(e)}\n")
            import traceback
            traceback.print_exc()
            return False

    async def test_vietnamese_question_generation(self):
        """Test 3: Generate questions in Vietnamese"""
        print("=" * 60)
        print("TEST 3: Vietnamese Question Generation")
        print("=" * 60)
        
        try:
            sample_text = """
            Quang hợp là quá trình mà thực vật và một số sinh vật khác sử dụng để chuyển đổi 
            năng lượng ánh sáng thành năng lượng hóa học. Năng lượng hóa học này được lưu trữ 
            trong các phân tử carbohydrate như đường và tinh bột, được tổng hợp từ carbon dioxide 
            và nước. Oxy được giải phóng như một sản phẩm phụ.
            """
            
            print(f"Sample text (Vietnamese): {sample_text[:100]}...")
            print(f"Generating 1 question in Vietnamese with easy difficulty...\n")
            
            result = await self.text_processor.generate_questions(
                text=sample_text,
                num_question=1,
                language="Vietnamese",
                difficulty="easy"
            )
            
            print(f"Generated {len(result['questions'])} questions:")
            for i, q in enumerate(result['questions'], 1):
                print(f"\nCâu hỏi {i}:")
                print(f"  Q: {q['question']}")
                print(f"  Đáp án: {q['options']}")
                print(f"  Đúng: {q['answer']} - {q['options'][q['answer']]}")
                print(f"  Giải thích: {q['explanation']}")
            
            print("\n✓ Test 3 PASSED\n")
            return True
        except Exception as e:
            print(f"✗ Test 3 FAILED: {str(e)}\n")
            import traceback
            traceback.print_exc()
            return False

    async def test_summarizer(self):
        """Test 4: Test text summarization (without images)"""
        print("=" * 60)
        print("TEST 4: Text Summarization")
        print("=" * 60)
        
        try:
            long_text = """
            Artificial Intelligence (AI) is intelligence demonstrated by machines, in contrast to 
            the natural intelligence displayed by humans and animals. Leading AI textbooks define 
            the field as the study of "intelligent agents": any device that perceives its environment 
            and takes actions that maximize its chance of successfully achieving its goals. 
            Colloquially, the term "artificial intelligence" is often used to describe machines 
            (or computers) that mimic "cognitive" functions that humans associate with the human 
            mind, such as "learning" and "problem solving". As machines become increasingly capable, 
            tasks considered to require "intelligence" are often removed from the definition of AI, 
            a phenomenon known as the AI effect. A quip in Tesler's Theorem says "AI is whatever 
            hasn't been done yet." For instance, optical character recognition is frequently excluded 
            from things considered to be AI, having become a routine technology.
            """
            
            print(f"Long text: {long_text[:150]}...")
            print(f"Requesting summary...\n")
            
            prompt = "Summarize the following text in 2-3 sentences:\n\n" + long_text
            response = await self.genai_client.model.generate_content_async(contents=prompt)
            
            print(f"Summary:\n{response.text}\n")
            print("✓ Test 4 PASSED\n")
            return True
        except Exception as e:
            print(f"✗ Test 4 FAILED: {str(e)}\n")
            return False

    async def test_different_difficulty_levels(self):
        """Test 5: Test different difficulty levels"""
        print("=" * 60)
        print("TEST 5: Different Difficulty Levels")
        print("=" * 60)
        
        try:
            sample_text = """
            The water cycle, also known as the hydrologic cycle, describes the continuous movement 
            of water on, above and below the surface of the Earth. Water can change states among 
            liquid, vapor, and ice at various places in the water cycle. The processes include 
            evaporation, condensation, precipitation, infiltration, surface runoff, and subsurface flow.
            """
            
            difficulties = ["easy", "medium", "hard"]
            
            for difficulty in difficulties:
                print(f"\n--- Testing {difficulty.upper()} difficulty ---")
                
                result = await self.text_processor.generate_questions(
                    text=sample_text,
                    num_question=1,
                    language="English",
                    difficulty=difficulty
                )
                
                if result['questions']:
                    q = result['questions'][0]
                    print(f"Question: {q['question'][:100]}...")
                    print(f"Options: {len(q['options'])} choices")
                    print(f"✓ {difficulty.capitalize()} question generated")
            
            print("\n✓ Test 5 PASSED\n")
            return True
        except Exception as e:
            print(f"✗ Test 5 FAILED: {str(e)}\n")
            import traceback
            traceback.print_exc()
            return False

    async def test_model_info(self):
        """Test 6: Get model information"""
        print("=" * 60)
        print("TEST 6: Model Information")
        print("=" * 60)
        
        try:
            print(f"Model: {self.genai_client.model._model_name}")
            print(f"System Instruction: {len(default_prompt)} characters")
            print("\n✓ Test 6 PASSED\n")
            return True
        except Exception as e:
            print(f"✗ Test 6 FAILED: {str(e)}\n")
            return False

    async def run_all_tests(self):
        """Run all tests"""
        print("\n" + "=" * 60)
        print("GEMINI API TESTING SUITE")
        print("=" * 60 + "\n")
        
        tests = [
            self.test_model_info,
            self.test_simple_text_generation,
            self.test_question_generation_from_text,
            self.test_vietnamese_question_generation,
            self.test_summarizer,
            self.test_different_difficulty_levels,
        ]
        
        results = []
        for test in tests:
            result = await test()
            results.append(result)
        
        # Summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        passed = sum(results)
        total = len(results)
        print(f"Passed: {passed}/{total}")
        print(f"Failed: {total - passed}/{total}")
        
        if passed == total:
            print("\n🎉 All tests PASSED!")
        else:
            print(f"\n⚠️  {total - passed} test(s) FAILED")
        
        print("=" * 60 + "\n")


async def main():
    """Main function to run tests"""
    try:
        tester = GeminiAPITester()
        await tester.run_all_tests()
    except Exception as e:
        print(f"Error initializing tester: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 Starting Gemini API Tests...\n")
    asyncio.run(main())
