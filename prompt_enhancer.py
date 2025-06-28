import openai
import json
import re
from typing import List, Dict, Optional, Tuple
import random

class PromptEnhancer:
    """
    Advanced prompt enhancement system for better AI video generation.
    Includes style suggestions, prompt optimization, and creative variations.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the prompt enhancer.
        
        Args:
            openai_api_key: OpenAI API key for GPT-based enhancements
        """
        self.openai_api_key = openai_api_key
        if openai_api_key:
            openai.api_key = openai_api_key
        
        # Predefined style modifiers
        self.style_modifiers = {
            'cinematic': [
                'cinematic lighting', 'dramatic shadows', 'film grain',
                'anamorphic lens', 'depth of field', 'golden hour lighting'
            ],
            'artistic': [
                'oil painting style', 'watercolor effect', 'impressionist',
                'abstract art', 'surreal', 'avant-garde'
            ],
            'realistic': [
                'photorealistic', 'high detail', 'sharp focus',
                'natural lighting', 'documentary style', 'candid'
            ],
            'fantasy': [
                'magical', 'ethereal', 'mystical atmosphere',
                'glowing effects', 'otherworldly', 'enchanted'
            ],
            'sci-fi': [
                'futuristic', 'cyberpunk', 'neon lights',
                'holographic', 'space age', 'technological'
            ],
            'vintage': [
                'retro', 'vintage film', 'sepia tone',
                'old-fashioned', 'nostalgic', 'classic'
            ]
        }
        
        # Camera movement suggestions
        self.camera_movements = [
            'slow zoom in', 'slow zoom out', 'pan left', 'pan right',
            'tilt up', 'tilt down', 'dolly forward', 'dolly backward',
            'orbital rotation', 'handheld movement', 'steady cam',
            'crane shot', 'tracking shot', 'push in'
        ]
        
        # Lighting conditions
        self.lighting_conditions = [
            'golden hour', 'blue hour', 'harsh sunlight', 'soft diffused light',
            'dramatic shadows', 'rim lighting', 'backlighting', 'side lighting',
            'neon lighting', 'candlelight', 'moonlight', 'studio lighting'
        ]
        
        # Quality enhancers
        self.quality_enhancers = [
            '4K resolution', 'high detail', 'sharp focus', 'professional quality',
            'award-winning', 'masterpiece', 'highly detailed', 'ultra-realistic'
        ]
    
    def enhance_prompt(self, base_prompt: str, style: str = 'cinematic',
                      add_camera_movement: bool = True,
                      add_lighting: bool = True,
                      add_quality_terms: bool = True) -> str:
        """
        Enhance a basic prompt with style, camera movement, and quality terms.
        
        Args:
            base_prompt: The original prompt
            style: Style category to apply
            add_camera_movement: Whether to add camera movement
            add_lighting: Whether to add lighting description
            add_quality_terms: Whether to add quality enhancers
        
        Returns:
            Enhanced prompt string
        """
        enhanced_parts = [base_prompt]
        
        # Add style modifiers
        if style in self.style_modifiers:
            style_terms = random.sample(self.style_modifiers[style], 
                                      min(2, len(self.style_modifiers[style])))
            enhanced_parts.extend(style_terms)
        
        # Add camera movement
        if add_camera_movement:
            movement = random.choice(self.camera_movements)
            enhanced_parts.append(movement)
        
        # Add lighting
        if add_lighting:
            lighting = random.choice(self.lighting_conditions)
            enhanced_parts.append(lighting)
        
        # Add quality terms
        if add_quality_terms:
            quality_terms = random.sample(self.quality_enhancers, 2)
            enhanced_parts.extend(quality_terms)
        
        return ', '.join(enhanced_parts)
    
    def generate_variations(self, base_prompt: str, num_variations: int = 5) -> List[str]:
        """
        Generate multiple variations of a prompt.
        
        Args:
            base_prompt: The original prompt
            num_variations: Number of variations to generate
        
        Returns:
            List of prompt variations
        """
        variations = []
        styles = list(self.style_modifiers.keys())
        
        for i in range(num_variations):
            style = random.choice(styles)
            variation = self.enhance_prompt(
                base_prompt,
                style=style,
                add_camera_movement=random.choice([True, False]),
                add_lighting=random.choice([True, False]),
                add_quality_terms=True
            )
            variations.append(variation)
        
        return variations
    
    def analyze_prompt(self, prompt: str) -> Dict[str, any]:
        """
        Analyze a prompt and provide suggestions for improvement.
        
        Args:
            prompt: The prompt to analyze
        
        Returns:
            Dictionary with analysis results and suggestions
        """
        analysis = {
            'word_count': len(prompt.split()),
            'has_style_terms': False,
            'has_camera_movement': False,
            'has_lighting': False,
            'has_quality_terms': False,
            'suggestions': []
        }
        
        prompt_lower = prompt.lower()
        
        # Check for existing style terms
        for style, terms in self.style_modifiers.items():
            if any(term.lower() in prompt_lower for term in terms):
                analysis['has_style_terms'] = True
                break
        
        # Check for camera movement
        if any(movement.lower() in prompt_lower for movement in self.camera_movements):
            analysis['has_camera_movement'] = True
        
        # Check for lighting
        if any(lighting.lower() in prompt_lower for lighting in self.lighting_conditions):
            analysis['has_lighting'] = True
        
        # Check for quality terms
        if any(quality.lower() in prompt_lower for quality in self.quality_enhancers):
            analysis['has_quality_terms'] = True
        
        # Generate suggestions
        if not analysis['has_style_terms']:
            analysis['suggestions'].append("Consider adding style terms like 'cinematic' or 'artistic'")
        
        if not analysis['has_camera_movement']:
            analysis['suggestions'].append("Add camera movement like 'slow zoom in' or 'pan left'")
        
        if not analysis['has_lighting']:
            analysis['suggestions'].append("Specify lighting conditions like 'golden hour' or 'dramatic shadows'")
        
        if analysis['word_count'] < 5:
            analysis['suggestions'].append("Consider making the prompt more descriptive")
        
        if analysis['word_count'] > 50:
            analysis['suggestions'].append("Consider shortening the prompt for better focus")
        
        return analysis
    
    def gpt_enhance_prompt(self, base_prompt: str, style_preference: str = "cinematic") -> Optional[str]:
        """
        Use GPT to enhance a prompt with more sophisticated language.
        
        Args:
            base_prompt: The original prompt
            style_preference: Preferred style for enhancement
        
        Returns:
            GPT-enhanced prompt or None if API not available
        """
        if not self.openai_api_key:
            return None
        
        try:
            system_prompt = f"""You are an expert at creating prompts for AI video generation. 
            Enhance the given prompt to be more descriptive and cinematic while maintaining the core concept.
            Focus on {style_preference} style. Add specific details about:
            - Visual composition and framing
            - Lighting and atmosphere
            - Camera movement or perspective
            - Color palette or mood
            - Technical quality descriptors
            
            Keep the enhanced prompt under 100 words and make it flow naturally."""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Enhance this prompt: {base_prompt}"}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error with GPT enhancement: {e}")
            return None
    
    def suggest_complementary_prompts(self, base_prompt: str) -> List[str]:
        """
        Suggest complementary prompts that would work well in a series.
        
        Args:
            base_prompt: The original prompt
        
        Returns:
            List of complementary prompts
        """
        # Extract key elements from the base prompt
        words = base_prompt.lower().split()
        
        # Define complementary concepts
        complementary_concepts = {
            'day': ['night', 'sunset', 'dawn'],
            'close': ['wide shot', 'aerial view', 'distant'],
            'calm': ['stormy', 'dramatic', 'intense'],
            'modern': ['vintage', 'retro', 'classic'],
            'indoor': ['outdoor', 'exterior', 'landscape'],
            'static': ['dynamic', 'moving', 'flowing']
        }
        
        suggestions = []
        
        # Generate time-based variations
        if any(word in words for word in ['day', 'morning', 'noon']):
            suggestions.append(base_prompt.replace('day', 'night').replace('morning', 'evening'))
        
        # Generate perspective variations
        if 'close' in words or 'closeup' in words:
            suggestions.append(base_prompt.replace('close', 'wide angle'))
        
        # Generate mood variations
        if any(word in words for word in ['calm', 'peaceful', 'serene']):
            dramatic_version = base_prompt + ', dramatic storm clouds, intense atmosphere'
            suggestions.append(dramatic_version)
        
        # Generate seasonal variations
        seasons = ['spring', 'summer', 'autumn', 'winter']
        for season in seasons:
            if season not in base_prompt.lower():
                seasonal_prompt = f"{base_prompt}, {season} setting"
                suggestions.append(seasonal_prompt)
                break
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def create_prompt_template(self, category: str) -> str:
        """
        Create a template prompt for a specific category.
        
        Args:
            category: Category like 'nature', 'urban', 'portrait', etc.
        
        Returns:
            Template prompt string
        """
        templates = {
            'nature': "A [adjective] [natural_element] in [location], [lighting], [camera_movement], [style]",
            'urban': "A [adjective] [urban_element] in [city_location], [time_of_day], [camera_movement], [style]",
            'portrait': "A [adjective] portrait of [subject], [lighting], [background], [camera_angle], [style]",
            'abstract': "Abstract [concept] with [colors], [movement], [texture], [lighting], [style]",
            'fantasy': "A [magical_element] in [fantasy_location], [magical_lighting], [camera_movement], [fantasy_style]"
        }
        
        return templates.get(category, "A [subject] in [location], [lighting], [camera_movement], [style]")
    
    def extract_keywords(self, prompt: str) -> List[str]:
        """
        Extract key visual elements from a prompt.
        
        Args:
            prompt: The prompt to analyze
        
        Returns:
            List of extracted keywords
        """
        # Remove common words and punctuation
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        # Clean and split the prompt
        cleaned_prompt = re.sub(r'[^\w\s]', '', prompt.lower())
        words = cleaned_prompt.split()
        
        # Filter out stop words and short words
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords[:10]  # Return top 10 keywords
    
    def get_style_recommendations(self, prompt: str) -> List[Tuple[str, str]]:
        """
        Get style recommendations based on prompt content.
        
        Args:
            prompt: The prompt to analyze
        
        Returns:
            List of (style_name, reason) tuples
        """
        prompt_lower = prompt.lower()
        recommendations = []
        
        # Analyze prompt content for style suggestions
        if any(word in prompt_lower for word in ['nature', 'landscape', 'forest', 'mountain', 'ocean']):
            recommendations.append(('cinematic', 'Natural scenes work well with cinematic lighting'))
        
        if any(word in prompt_lower for word in ['city', 'urban', 'street', 'building']):
            recommendations.append(('sci-fi', 'Urban environments suit futuristic styling'))
        
        if any(word in prompt_lower for word in ['person', 'face', 'portrait', 'character']):
            recommendations.append(('realistic', 'Portraits benefit from realistic rendering'))
        
        if any(word in prompt_lower for word in ['dream', 'fantasy', 'magic', 'surreal']):
            recommendations.append(('fantasy', 'Fantastical elements suit magical styling'))
        
        if any(word in prompt_lower for word in ['old', 'vintage', 'retro', 'classic']):
            recommendations.append(('vintage', 'Vintage themes work with retro styling'))
        
        # Default recommendation if no specific matches
        if not recommendations:
            recommendations.append(('cinematic', 'Cinematic style works well for most subjects'))
        
        return recommendations

# Example usage and testing
if __name__ == "__main__":
    enhancer = PromptEnhancer()
    
    # Test basic enhancement
    basic_prompt = "A cat sitting in a garden"
    enhanced = enhancer.enhance_prompt(basic_prompt, style='cinematic')
    print(f"Original: {basic_prompt}")
    print(f"Enhanced: {enhanced}")
    
    # Test variations
    variations = enhancer.generate_variations(basic_prompt, 3)
    print(f"\nVariations:")
    for i, variation in enumerate(variations, 1):
        print(f"{i}. {variation}")
    
    # Test analysis
    analysis = enhancer.analyze_prompt(basic_prompt)
    print(f"\nAnalysis: {analysis}")
    
    print("\nPrompt enhancer initialized successfully!")