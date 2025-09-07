import os
import json
import requests
from typing import Dict, List, Any, TypedDict
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from datetime import datetime
import base64
from pathlib import Path
import re
import traceback

# State definition for the agent
class SlideshowState(TypedDict):
    topic: str
    num_slides: int
    outline: List[Dict[str, Any]]
    slides_content: List[Dict[str, Any]]
    images: List[Dict[str, str]]
    html_output: str
    current_slide: int
    error: str

class SlideshowAgent:
    def __init__(self, groq_api_key: str, unsplash_access_key: str = None):
        self.llm = ChatGroq(
            api_key=groq_api_key,
            model="deepseek-r1-distill-llama-70b",
            temperature=0.7,
            max_tokens=4000,  # Reduced for more reliable responses
            timeout=120
        )
        self.unsplash_key = unsplash_access_key
        
    def _extract_json_from_response(self, text: str) -> Dict:
        """Extract JSON from DeepSeek response, handling various formats"""
        try:
            print(f"Raw response: {text[:500]}...")  # Debug print
            
            # Clean the text
            text = text.strip()
            
            # Try to find JSON in various formats
            json_patterns = [
                r'\{.*\}',  # Standard JSON
                r'```json\s*(\{.*?\})\s*```',  # JSON in code blocks
                r'```\s*(\{.*?\})\s*```',  # JSON in generic code blocks
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, text, re.DOTALL)
                for match in matches:
                    try:
                        if isinstance(match, tuple):
                            match = match[0] if match else text
                        return json.loads(match)
                    except json.JSONDecodeError:
                        continue
            
            # If no JSON found in patterns, try the whole text
            return json.loads(text)
            
        except Exception as e:
            print(f"JSON extraction failed: {e}")
            return None
        
    def create_outline_node(self, state: SlideshowState) -> SlideshowState:
        """Generate a detailed outline for the slideshow"""
        try:
            print(f"Creating outline for: {state['topic']} ({state['num_slides']} slides)")
            
            messages = [
                SystemMessage(content="You are an expert presentation designer. Create detailed slideshow outlines. Respond ONLY with valid JSON."),
                HumanMessage(content=f"""Create an outline for a {state['num_slides']}-slide presentation about "{state['topic']}".

Return ONLY this JSON format:
{{
    "slides": [
        {{
            "slide_number": 1,
            "title": "Introduction to {state['topic']}",
            "type": "title",
            "main_points": ["Welcome", "Overview", "Goals"],
            "image_description": "professional presentation background",
            "speaker_notes": "Introduction slide"
        }},
        {{
            "slide_number": 2,
            "title": "Key Concepts",
            "type": "content",
            "main_points": ["Point 1", "Point 2", "Point 3"],
            "image_description": "relevant illustration",
            "speaker_notes": "Main content"
        }}
    ]
}}""")
            ]
            
            response = self.llm.invoke(messages)
            print(f"Outline response received: {len(response.content)} chars")
            
            outline_data = self._extract_json_from_response(response.content)
            
            if not outline_data or "slides" not in outline_data:
                # Create fallback outline
                print("Creating fallback outline...")
                outline_data = self._create_fallback_outline(state['topic'], state['num_slides'])
            
            state["outline"] = outline_data["slides"]
            print(f"Outline created with {len(state['outline'])} slides")
            return state
            
        except Exception as e:
            print(f"Error in create_outline_node: {e}")
            traceback.print_exc()
            # Create fallback outline
            outline_data = self._create_fallback_outline(state['topic'], state['num_slides'])
            state["outline"] = outline_data["slides"]
            return state
    
    def _create_fallback_outline(self, topic: str, num_slides: int) -> Dict:
        """Create a fallback outline if AI generation fails"""
        slides = []
        slides.append({
            "slide_number": 1,
            "title": f"Introduction to {topic}",
            "type": "title",
            "main_points": ["Welcome", "Overview", "Agenda"],
            "image_description": "professional presentation background",
            "speaker_notes": "Introduction slide"
        })
        
        for i in range(2, num_slides):
            slides.append({
                "slide_number": i,
                "title": f"{topic} - Part {i-1}",
                "type": "content",
                "main_points": [f"Key point {j+1}" for j in range(3)],
                "image_description": f"illustration related to {topic}",
                "speaker_notes": f"Content slide {i}"
            })
        
        if num_slides > 1:
            slides.append({
                "slide_number": num_slides,
                "title": "Conclusion",
                "type": "conclusion",
                "main_points": ["Summary", "Key takeaways", "Thank you"],
                "image_description": "conclusion or thank you image",
                "speaker_notes": "Conclusion slide"
            })
        
        return {"slides": slides}
    
    def generate_content_node(self, state: SlideshowState) -> SlideshowState:
        """Generate detailed content for each slide"""
        try:
            print("Generating content for slides...")
            slides_content = []
            
            for i, slide_info in enumerate(state["outline"]):
                print(f"Generating content for slide {i+1}/{len(state['outline'])}")
                
                try:
                    messages = [
                        SystemMessage(content="You are a content writer. Create engaging slide content. Respond ONLY with valid JSON."),
                        HumanMessage(content=f"""Create content for slide {slide_info['slide_number']}: "{slide_info['title']}"

Main points: {slide_info['main_points']}

Return ONLY this JSON:
{{
    "slide_number": {slide_info['slide_number']},
    "title": "{slide_info['title']}",
    "content": "Detailed content about this topic. Keep it engaging and informative.",
    "bullet_points": ["Expanded point 1", "Expanded point 2", "Expanded point 3"],
    "supporting_info": "Additional context and supporting information",
    "image_description": "{slide_info.get('image_description', 'relevant image')}"
}}""")
                    ]
                    
                    response = self.llm.invoke(messages)
                    slide_content = self._extract_json_from_response(response.content)
                    
                    if not slide_content:
                        # Create fallback content
                        slide_content = {
                            "slide_number": slide_info['slide_number'],
                            "title": slide_info['title'],
                            "content": f"This slide covers important aspects of {slide_info['title']}. It provides comprehensive information and insights that are valuable for understanding the topic.",
                            "bullet_points": slide_info['main_points'],
                            "supporting_info": "Additional context and detailed information to support the main content.",
                            "image_description": slide_info.get('image_description', 'relevant image')
                        }
                    
                    slides_content.append(slide_content)
                    
                except Exception as e:
                    print(f"Error generating content for slide {i+1}: {e}")
                    # Add fallback content
                    slides_content.append({
                        "slide_number": slide_info['slide_number'],
                        "title": slide_info['title'],
                        "content": f"Content for {slide_info['title']}",
                        "bullet_points": slide_info['main_points'],
                        "supporting_info": "Supporting information",
                        "image_description": slide_info.get('image_description', 'relevant image')
                    })
            
            state["slides_content"] = slides_content
            print(f"Generated content for {len(slides_content)} slides")
            return state
            
        except Exception as e:
            print(f"Error in generate_content_node: {e}")
            traceback.print_exc()
            state["error"] = f"Error generating content: {str(e)}"
            return state
    
    def fetch_images_node(self, state: SlideshowState) -> SlideshowState:
        """Fetch relevant images from Unsplash API or use placeholders"""
        try:
            print("Fetching images...")
            images = []
            
            for slide in state["slides_content"]:
                try:
                    if self.unsplash_key:
                        # Try Unsplash API
                        search_query = slide.get("image_description", "business presentation")
                        url = f"https://api.unsplash.com/search/photos"
                        headers = {"Authorization": f"Client-ID {self.unsplash_key}"}
                        params = {"query": search_query, "per_page": 1, "orientation": "landscape"}
                        
                        response = requests.get(url, headers=headers, params=params, timeout=10)
                        
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("results"):
                                image_url = data["results"][0]["urls"]["regular"]
                                alt_text = data["results"][0].get("alt_description") or search_query
                            else:
                                image_url = f"https://picsum.photos/800/600?random={slide['slide_number']}"
                                alt_text = search_query
                        else:
                            image_url = f"https://picsum.photos/800/600?random={slide['slide_number']}"
                            alt_text = search_query
                    else:
                        # Use placeholder images
                        image_url = f"https://picsum.photos/800/600?random={slide['slide_number']}"
                        alt_text = slide.get("image_description", "Slide image")
                    
                    images.append({
                        "slide_number": slide["slide_number"],
                        "url": image_url,
                        "alt_text": alt_text
                    })
                    
                except Exception as e:
                    print(f"Error fetching image for slide {slide['slide_number']}: {e}")
                    # Fallback image
                    images.append({
                        "slide_number": slide["slide_number"],
                        "url": f"https://picsum.photos/800/600?random={slide['slide_number']}",
                        "alt_text": "Slide image"
                    })
            
            state["images"] = images
            print(f"Fetched {len(images)} images")
            return state
            
        except Exception as e:
            print(f"Error in fetch_images_node: {e}")
            traceback.print_exc()
            state["error"] = f"Error fetching images: {str(e)}"
            return state
    
    def generate_html_node(self, state: SlideshowState) -> SlideshowState:
        """Generate the final HTML slideshow"""
        try:
            print("Generating HTML...")
            
            if not state["slides_content"]:
                state["error"] = "No slides content available"
                return state
            
            # Create image mapping for easy lookup
            image_map = {img["slide_number"]: img for img in state["images"]}
            
            # Generate HTML
            html_content = self._create_html_template(state["topic"], state["slides_content"], image_map)
            
            state["html_output"] = html_content
            print(f"Generated HTML: {len(html_content)} characters")
            return state
            
        except Exception as e:
            print(f"Error in generate_html_node: {e}")
            traceback.print_exc()
            state["error"] = f"Error generating HTML: {str(e)}"
            return state
    
    def _create_html_template(self, topic: str, slides: List[Dict], image_map: Dict) -> str:
        """Create the HTML template with modern design"""
        
        if not slides:
            return "<html><body><h1>Error: No slides to display</h1></body></html>"
        
        slides_html = ""
        for slide in slides:
            slide_num = slide["slide_number"]
            image_info = image_map.get(slide_num, {"url": "https://picsum.photos/800/600", "alt_text": "Image"})
            
            # Escape HTML characters in content
            title = str(slide.get('title', f'Slide {slide_num}')).replace('<', '&lt;').replace('>', '&gt;')
            content = str(slide.get('content', '')).replace('<', '&lt;').replace('>', '&gt;')
            
            if slide_num == 1:
                # Title slide
                slides_html += f"""
                <div class="slide title-slide">
                    <div class="slide-content">
                        <h1>{title}</h1>
                        <div class="subtitle">{topic}</div>
                        <div class="slide-image">
                            <img src="{image_info['url']}" alt="{image_info['alt_text']}" loading="lazy">
                        </div>
                    </div>
                </div>
                """
            else:
                # Regular content slide
                bullet_points = ""
                if slide.get("bullet_points"):
                    bullet_points = "<ul>"
                    for point in slide["bullet_points"]:
                        safe_point = str(point).replace('<', '&lt;').replace('>', '&gt;')
                        bullet_points += f"<li>{safe_point}</li>"
                    bullet_points += "</ul>"
                
                supporting_info = ""
                if slide.get("supporting_info"):
                    safe_info = str(slide["supporting_info"]).replace('<', '&lt;').replace('>', '&gt;')
                    supporting_info = f'<div class="supporting-info"><p>{safe_info}</p></div>'
                
                slides_html += f"""
                <div class="slide">
                    <div class="slide-header">
                        <h2>{title}</h2>
                    </div>
                    <div class="slide-body">
                        <div class="slide-content">
                            <div class="content-text">
                                <p>{content}</p>
                                {bullet_points}
                                {supporting_info}
                            </div>
                        </div>
                        <div class="slide-image">
                            <img src="{image_info['url']}" alt="{image_info['alt_text']}" loading="lazy">
                        </div>
                    </div>
                </div>
                """
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic} - Presentation</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            overflow-x: hidden;
        }}
        
        .slideshow-container {{
            position: relative;
            max-width: 100%;
            margin: auto;
            background: white;
            min-height: 100vh;
        }}
        
        .slide {{
            display: none;
            padding: 40px;
            min-height: 100vh;
            background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
            position: relative;
            animation: slideIn 0.8s ease-in-out;
        }}
        
        .slide.active {{
            display: block;
        }}
        
        .title-slide {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .title-slide h1 {{
            font-size: 3.5rem;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            animation: titleGlow 2s ease-in-out infinite alternate;
        }}
        
        .subtitle {{
            font-size: 1.5rem;
            opacity: 0.9;
            margin-bottom: 40px;
        }}
        
        .slide-header {{
            border-bottom: 3px solid #667eea;
            margin-bottom: 30px;
            padding-bottom: 15px;
        }}
        
        .slide-header h2 {{
            font-size: 2.5rem;
            color: #667eea;
            font-weight: 700;
        }}
        
        .slide-body {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
            align-items: start;
        }}
        
        .slide-content {{
            line-height: 1.6;
        }}
        
        .content-text p {{
            font-size: 1.2rem;
            margin-bottom: 20px;
            color: #555;
        }}
        
        .slide ul {{
            list-style: none;
            padding-left: 0;
        }}
        
        .slide li {{
            font-size: 1.1rem;
            margin-bottom: 15px;
            padding-left: 30px;
            position: relative;
            color: #666;
        }}
        
        .slide li:before {{
            content: "→";
            position: absolute;
            left: 0;
            color: #667eea;
            font-weight: bold;
            font-size: 1.2rem;
        }}
        
        .supporting-info {{
            background: linear-gradient(90deg, #f8f9fa, #e9ecef);
            padding: 20px;
            border-left: 4px solid #667eea;
            margin-top: 20px;
            border-radius: 0 8px 8px 0;
        }}
        
        .supporting-info p {{
            font-style: italic;
            color: #666;
            margin-bottom: 0;
        }}
        
        .slide-image {{
            position: relative;
            overflow: hidden;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }}
        
        .slide-image:hover {{
            transform: scale(1.02);
        }}
        
        .slide-image img {{
            width: 100%;
            height: 400px;
            object-fit: cover;
            border-radius: 15px;
        }}
        
        .title-slide .slide-image img {{
            height: 300px;
            margin-top: 30px;
        }}
        
        .nav-buttons {{
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 15px;
            z-index: 1000;
        }}
        
        .nav-btn {{
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }}
        
        .nav-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }}
        
        .nav-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }}
        
        .slide-counter {{
            position: fixed;
            top: 30px;
            right: 30px;
            background: rgba(255, 255, 255, 0.9);
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: bold;
            color: #667eea;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateX(50px);
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}
        
        @keyframes titleGlow {{
            from {{
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            to {{
                text-shadow: 2px 2px 20px rgba(255,255,255,0.5);
            }}
        }}
        
        @media (max-width: 768px) {{
            .slide {{
                padding: 20px;
            }}
            
            .slide-body {{
                grid-template-columns: 1fr;
                gap: 20px;
            }}
            
            .title-slide h1 {{
                font-size: 2.5rem;
            }}
            
            .slide-header h2 {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="slideshow-container">
        {slides_html}
    </div>
    
    <div class="slide-counter">
        <span id="current-slide">1</span> / <span id="total-slides">{len(slides)}</span>
    </div>
    
    <div class="nav-buttons">
        <button class="nav-btn" id="prev-btn" onclick="changeSlide(-1)">← Previous</button>
        <button class="nav-btn" id="next-btn" onclick="changeSlide(1)">Next →</button>
    </div>
    
    <script>
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');
        const totalSlides = slides.length;
        
        function showSlide(n) {{
            slides[currentSlide].classList.remove('active');
            currentSlide = (n + totalSlides) % totalSlides;
            slides[currentSlide].classList.add('active');
            
            document.getElementById('current-slide').textContent = currentSlide + 1;
            
            document.getElementById('prev-btn').disabled = currentSlide === 0;
            document.getElementById('next-btn').disabled = currentSlide === totalSlides - 1;
        }}
        
        function changeSlide(n) {{
            if (currentSlide + n >= 0 && currentSlide + n < totalSlides) {{
                showSlide(currentSlide + n);
            }}
        }}
        
        showSlide(0);
        
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'ArrowLeft') changeSlide(-1);
            if (e.key === 'ArrowRight') changeSlide(1);
        }});
    </script>
</body>
</html>"""
    
    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(SlideshowState)
        
        # Add nodes
        workflow.add_node("create_outline", self.create_outline_node)
        workflow.add_node("generate_content", self.generate_content_node)
        workflow.add_node("fetch_images", self.fetch_images_node)
        workflow.add_node("generate_html", self.generate_html_node)
        
        # Define edges
        workflow.set_entry_point("create_outline")
        workflow.add_edge("create_outline", "generate_content")
        workflow.add_edge("generate_content", "fetch_images")
        workflow.add_edge("fetch_images", "generate_html")
        workflow.add_edge("generate_html", END)
        
        return workflow.compile()

# Enhanced usage function with better error handling
def create_slideshow(topic: str, num_slides: int = 10, groq_api_key: str = None, unsplash_key: str = None):
    """
    Create a slideshow using the LangGraph agent with Groq and DeepSeek R1
    
    Args:
        topic: The topic for the slideshow
        num_slides: Number of slides (up to 70)
        groq_api_key: Groq API key (required)
        unsplash_key: Unsplash API key (optional)
    """
    
    if not groq_api_key:
        raise ValueError("Groq API key is required. Get one from https://console.groq.com/")
    
    print(f"Creating slideshow: '{topic}' with {num_slides} slides")
    
    try:
        # Initialize the agent
        agent = SlideshowAgent(groq_api_key, unsplash_key)
        print("Agent initialized successfully")
        
        # Build the graph
        app = agent.build_graph()
        print("Workflow graph built successfully")
        
        # Initial state
        initial_state = {
            "topic": topic,
            "num_slides": min(num_slides, 70),  # Cap at 70 slides
            "outline": [],
            "slides_content": [],
            "images": [],
            "html_output": "",
            "current_slide": 0,
            "error": ""
        }
        
        print("Starting workflow execution...")
        
        # Run the workflow
        result = app.invoke(initial_state)
        
        print("Workflow completed")
        
        if result.get("error"):
            print(f"Workflow error: {result['error']}")
            return None
        
        if not result.get("html_output"):
            print("Error: No HTML output generated")
            return None
        
        # Save the HTML file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '_', '-')).strip()
        safe_topic = safe_topic.replace(' ', '_')
        filename = f"slideshow_{safe_topic}_{timestamp}.html"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(result["html_output"])
        
        file_size = os.path.getsize(filename)
        print(f"✅ Slideshow created successfully!")
        print(f"📁 File: {filename}")
        print(f"📊 Size: {file_size:,} bytes")
        print(f"🎯 Slides: {len(result.get('slides_content', []))}")
        
        return filename
        
    except Exception as e:
        print(f"❌ Error creating slideshow: {e}")
        traceback.print_exc()
        return None

# Example usage with better error messages
if __name__ == "__main__":
    print("🚀 DeepSeek R1 Slideshow Generator")
    print("=" * 50)
    
    # Example usage
    slideshow_file = create_slideshow(
        topic="Mastering n8n: From Beginner to Professional Automation",
        num_slides=40,
        groq_api_key="API",
        unsplash_key="API"  # Optional
    )
    
    if slideshow_file:
        print(f"\n🎉 Open {slideshow_file} in your browser to view the slideshow!")
    else:
        print("\n❌ Failed to create slideshow. Check the error messages above.")
    