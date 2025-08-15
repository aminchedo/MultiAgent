#!/usr/bin/env python3
"""
Hugging Face Spaces deployment entry point.
Creates a Gradio interface for the Multi-Agent Code Generation System.
"""

import os
import sys
import asyncio
import gradio as gr
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set HF environment
os.environ["HUGGINGFACE_SPACES"] = "1"

def setup_gradio_interface():
    """Set up the Gradio interface for Hugging Face Spaces"""
    
    async def generate_code(prompt: str, project_type: str = "web_app"):
        """Generate code using the multi-agent system"""
        try:
            # Import the main application components
            from backend.agents.manager import AgentManager
            from backend.models.requests import CodeGenerationRequest
            
            # Create request
            request = CodeGenerationRequest(
                prompt=prompt,
                project_type=project_type,
                user_id="huggingface_user"
            )
            
            # Initialize agent manager
            manager = AgentManager()
            
            # Generate code
            result = await manager.generate_code(request)
            
            return result.generated_code, result.explanation
            
        except Exception as e:
            return f"Error: {str(e)}", "Code generation failed"
    
    def sync_generate_code(prompt: str, project_type: str):
        """Synchronous wrapper for async code generation"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            code, explanation = loop.run_until_complete(generate_code(prompt, project_type))
            loop.close()
            return code, explanation
        except Exception as e:
            return f"Error: {str(e)}", "Failed to generate code"
    
    # Create Gradio interface
    with gr.Blocks(
        title="Multi-Agent Code Generator",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            font-family: 'Arial', sans-serif;
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            padding: 20px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        """
    ) as demo:
        
        gr.HTML("""
        <div class="header">
            <h1>🤖 Multi-Agent Code Generation System</h1>
            <p>AI-powered code generation using multiple specialized agents</p>
        </div>
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                prompt_input = gr.Textbox(
                    label="Code Generation Prompt",
                    placeholder="Describe what you want to build (e.g., 'Create a todo app with React and FastAPI')",
                    lines=5,
                    value="Create a simple web application with user authentication"
                )
                
                project_type = gr.Dropdown(
                    label="Project Type",
                    choices=[
                        "web_app",
                        "api",
                        "cli_tool",
                        "data_analysis",
                        "ml_model",
                        "automation_script"
                    ],
                    value="web_app"
                )
                
                generate_btn = gr.Button("🚀 Generate Code", variant="primary", size="lg")
            
            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.TabItem("Generated Code"):
                        code_output = gr.Code(
                            label="Generated Code",
                            language="python",
                            lines=20
                        )
                    
                    with gr.TabItem("Explanation"):
                        explanation_output = gr.Textbox(
                            label="Code Explanation",
                            lines=15,
                            max_lines=20
                        )
        
        # Connect the generate button
        generate_btn.click(
            fn=sync_generate_code,
            inputs=[prompt_input, project_type],
            outputs=[code_output, explanation_output],
            api_name="generate_code"
        )
        
        gr.HTML("""
        <div style="text-align: center; margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
            <p><strong>Features:</strong> Planning Agent • Code Generation • Quality Assurance • Testing • Documentation</p>
            <p><em>Powered by OpenAI GPT and specialized AI agents</em></p>
        </div>
        """)
    
    return demo

def main():
    """Main entry point for Hugging Face Spaces"""
    
    print("🚀 Starting Multi-Agent Code Generation System on Hugging Face Spaces...")
    
    # Verify environment
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set. Some features may not work.")
    
    # Create and launch Gradio interface
    try:
        demo = setup_gradio_interface()
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True
        )
    except Exception as e:
        print(f"❌ Failed to start Gradio interface: {e}")
        
        # Fallback simple interface
        def simple_interface(prompt):
            return f"Simple echo: {prompt}", "This is a fallback interface"
        
        simple_demo = gr.Interface(
            fn=simple_interface,
            inputs=gr.Textbox(label="Prompt"),
            outputs=[gr.Textbox(label="Output"), gr.Textbox(label="Info")],
            title="Multi-Agent Code Generator (Fallback Mode)"
        )
        simple_demo.launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    main()