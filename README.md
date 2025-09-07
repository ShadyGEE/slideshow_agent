# DeepSeek R1 Slideshow Generator

An intelligent slideshow generator that creates professional HTML presentations using AI-powered content generation. Built with LangGraph, Groq's DeepSeek R1 model, and modern web technologies.

## Features

- **AI-Powered Content**: Uses DeepSeek R1 via Groq for intelligent content generation
- **Professional Design**: Modern, responsive HTML slideshows with animations
- **Image Integration**: Automatic image fetching from Unsplash API or placeholder images
- **Interactive Navigation**: Keyboard and button navigation support
- **Robust Error Handling**: Fallback mechanisms ensure successful slideshow generation
- **Scalable**: Support for up to 70 slides per presentation
- **Mobile Responsive**: Adapts to different screen sizes

## Quick Start

### Prerequisites

- Python 3.8+
- Groq API key (required)
- Unsplash API key (optional, for better images)

### Installation

1. Clone or download the `slideshow_agent.py` file

2. Install required dependencies:
```bash
pip install langgraph langchain-groq requests pathlib
```

3. Get your API keys:
   - **Groq API Key**: Sign up at [console.groq.com](https://console.groq.com/)
   - **Unsplash API Key** (optional): Sign up at [unsplash.com/developers](https://unsplash.com/developers)

### Basic Usage

```python
from slideshow_agent import create_slideshow

# Create a slideshow
slideshow_file = create_slideshow(
    topic="Introduction to Machine Learning",
    num_slides=10,
    groq_api_key="your_groq_api_key_here",
    unsplash_key="your_unsplash_key_here"  # Optional
)

if slideshow_file:
    print(f"Slideshow created: {slideshow_file}")
```

### Command Line Usage

Run the script directly:

```bash
python slideshow_agent.py
```

Edit the example at the bottom of the file to customize your slideshow topic and settings.

## Generated Slideshow Features

### Visual Design
- **Modern Gradient Backgrounds**: Beautiful color schemes
- **Responsive Layout**: Works on desktop, tablet, and mobile
- **Smooth Animations**: Slide transitions and hover effects
- **Professional Typography**: Clean, readable fonts

### Navigation
- **Button Navigation**: Previous/Next buttons
- **Keyboard Support**: Arrow keys for navigation
- **Progress Counter**: Shows current slide number
- **Disabled State**: Buttons disabled at start/end

### Content Structure
- **Title Slide**: Eye-catching introduction
- **Content Slides**: Structured with headers, bullet points, and images
- **Supporting Information**: Additional context boxes
- **Image Integration**: Relevant images for each slide

## Configuration

### Function Parameters

```python
create_slideshow(
    topic: str,              # Main topic of the presentation
    num_slides: int = 10,    # Number of slides (max 70)
    groq_api_key: str = None,# Required: Your Groq API key
    unsplash_key: str = None # Optional: Unsplash API key
)
```

### Environment Variables (Alternative)

You can also set API keys as environment variables:

```bash
export GROQ_API_KEY="your_groq_api_key"
export UNSPLASH_ACCESS_KEY="your_unsplash_key"
```

## Architecture

The slideshow generator uses a **LangGraph workflow** with the following nodes:

1. **Create Outline**: Generates slide structure and topics
2. **Generate Content**: Creates detailed content for each slide
3. **Fetch Images**: Retrieves relevant images from Unsplash or placeholders
4. **Generate HTML**: Compiles everything into a beautiful HTML presentation

```
[Topic Input] → [Create Outline] → [Generate Content] → [Fetch Images] → [Generate HTML] → [Final Slideshow]
```

## Example Use Cases

Perfect for creating slideshows on topics such as:

- **Technology**: "Introduction to Blockchain Technology"
- **Business**: "Digital Marketing Strategies for 2024"
- **Education**: "Advanced Python Programming Concepts"
- **Science**: "Climate Change: Causes and Solutions"
- **Professional Development**: "Strategic Career Planning"

## Output Format

The generator creates an HTML file with:
- **Filename**: `slideshow_[topic]_[timestamp].html`
- **Self-contained**: All CSS and JavaScript embedded
- **Portable**: Can be shared and viewed on any browser
- **Professional**: Ready for presentations

## Troubleshooting

### Common Issues

1. **Missing API Key Error**
   ```
   ValueError: Groq API key is required
   ```
   **Solution**: Ensure you provide a valid Groq API key

2. **JSON Parsing Errors**
   ```
   JSON extraction failed
   ```
   **Solution**: The system automatically falls back to default content

3. **Image Loading Issues**
   - Without Unsplash key: Uses Lorem Picsum placeholders
   - With invalid Unsplash key: Falls back to placeholders

### Performance Optimization

- **Slide Limit**: Keep under 70 slides for optimal performance
- **Topic Clarity**: Use specific, clear topics for better content generation
- **API Limits**: Be aware of Groq API rate limits for large slideshows

## API Keys & Authentication

### Obtaining API Keys

1. **Groq (Required)**:
   - Visit [console.groq.com](https://console.groq.com/)
   - Sign up for free account
   - Generate API key in dashboard

2. **Unsplash (Optional)**:
   - Visit [unsplash.com/developers](https://unsplash.com/developers)
   - Create developer account
   - Register new application
   - Get access key

### Security Best Practices

- Never commit API keys to version control
- Use environment variables for production deployments
- Rotate keys regularly
- Monitor API usage and quotas

## Technical Specifications

- **AI Model**: DeepSeek R1 Distill (70B parameters)
- **Framework**: LangGraph for workflow orchestration
- **Image Source**: Unsplash API with Lorem Picsum fallback
- **Output**: Self-contained HTML5 with embedded CSS/JavaScript
- **Browser Support**: Modern browsers (Chrome, Firefox, Safari, Edge)
- **Python Requirements**: Python 3.8+ with specified dependencies

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is open source and available under the MIT License.

## Support

If you encounter issues:

1. Review the troubleshooting section
2. Verify your API keys are valid and have sufficient quota
3. Ensure all dependencies are properly installed
4. Check your internet connection for API calls

For additional support, please open an issue with detailed information about your environment and the specific problem encountered.

## Advanced Usage

### Custom Styling

You can modify the HTML template in the `_create_html_template` method to customize:
- Colors and theme variations
- Typography and font selections
- Layout and spacing adjustments
- Animation effects and transitions

### Extending Functionality

The modular design allows for:
- Implementation of additional content generation strategies
- Integration of alternative image sources
- Development of custom export formats
- Addition of presentation analytics and tracking

### Integration Options

This slideshow generator can be integrated into:
- Web applications via API endpoints
- Command-line tools for batch processing
- Educational platforms for automated content creation
- Content management systems for dynamic presentations

---