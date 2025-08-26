# Assets Directory - MultiAgent Vibe Coding Platform

This directory contains static assets and resources for the frontend application.

## Current Contents

### `favicon.ico`
- **Type**: Dependencies file (incorrectly named)
- **Purpose**: Contains Python package dependencies for the backend
- **Note**: This file appears to be misplaced and should be renamed or moved
- **Content**: FastAPI and related Python dependencies

### `index.html`
- **Type**: Alternative frontend interface
- **Language**: Persian/Farsi (RTL layout)
- **Purpose**: Internationalized version of the platform
- **Features**: Complete AI agent interface with Persian UI
- **Note**: This is a separate implementation from the main English frontend

## Recommended Structure

For proper asset organization, this directory should contain:

```
assets/
├── css/           # Stylesheet files
├── js/            # JavaScript modules
├── images/        # Image assets (logos, icons, etc.)
├── fonts/         # Custom font files
└── icons/         # Icon sets and favicons
```

## Usage Notes

- The main frontend files (`enhanced_vibe_frontend.html`, `test_vibe_integration.html`) currently embed all styles and scripts inline
- Future development should extract these to separate files in this assets directory
- The Persian interface (`index.html`) represents an alternative localized version of the platform
- Consider organizing assets by component or feature for better maintainability

## Development Guidelines

1. **Styles**: Extract embedded CSS to separate files in `assets/css/`
2. **Scripts**: Move reusable JavaScript to `assets/js/`
3. **Images**: Store all image assets in `assets/images/`
4. **Icons**: Use a consistent icon system (Material Design, Font Awesome, etc.)
5. **Fonts**: Host custom fonts locally for better performance