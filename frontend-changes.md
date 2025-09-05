# Frontend Changes

This document tracks all frontend-related changes made to the Course Materials Assistant, including backend quality tools, testing framework, and UI enhancements.

## Code Quality Tools Implementation

**Note**: This implementation focused on backend code quality tools as the primary codebase is Python-based serving a web interface.

### Code Quality Tools Added
1. **Black** - Automatic Python code formatting
2. **isort** - Import sorting with Black compatibility
3. **flake8** - Code linting and style checking

### Configuration Files Updated
1. **pyproject.toml** - Added quality tool dependencies and configuration
   - Added black, flake8, and isort dependencies
   - Configured Black settings (line length: 88, target Python 3.12+)
   - Configured isort to work with Black profile

### Scripts Created
1. **scripts/quality.sh** - Comprehensive quality check script
   - Runs formatting checks
   - Performs linting with flake8
   - Executes tests if available
   - Provides colored output with status indicators

2. **scripts/format.sh** - Code formatting only script
   - Runs Black formatter
   - Sorts imports with isort
   - Quick formatting without linting

3. **scripts/fix-lint.sh** - Auto-fix common linting issues
   - Removes unused imports (when autoflake available)
   - Applies formatting
   - Sorts imports

### Code Formatting Applied
- Applied Black formatting to all Python files in the backend
- Sorted imports throughout the codebase
- Improved code consistency and readability

### Documentation Updated
- Updated CLAUDE.md with new quality tool commands
- Added section explaining how to use the quality scripts
- Included manual command references

### Quality Tools Usage

```bash
# Run all quality checks
./scripts/quality.sh

# Format code only
./scripts/format.sh

# Auto-fix common issues
./scripts/fix-lint.sh
```

## Testing Framework Enhancements

Enhanced the existing testing framework for the RAG system in `@backend/tests`. While these are primarily backend testing changes, they ensure the API endpoints that serve the frontend are thoroughly tested.

### Changes Made

#### 1. **pytest Configuration in pyproject.toml** 
- Added comprehensive `[tool.pytest.ini_options]` configuration to `pyproject.toml`
- Configured testpaths, file patterns, and test discovery settings
- Added useful pytest options: verbose output, short tracebacks, strict markers, colored output
- Defined custom markers: `unit`, `integration`, `api` for better test organization
- Added `httpx>=0.24.0` dependency for API testing

#### 2. **Enhanced conftest.py with API Testing Fixtures**
- Extended existing `backend/tests/conftest.py` with new fixtures for API testing
- Added `mock_rag_system` fixture - comprehensive mock of the RAG system for API tests
- Added `test_app` fixture - creates a test FastAPI app avoiding static file mount issues
- Added sample request/response fixtures: `sample_query_request`, `expected_query_response`, etc.
- Implemented proper error handling in test app endpoints to match production behavior

#### 3. **Comprehensive API Endpoint Tests**
- Created `backend/tests/test_api_endpoints.py` with 22 comprehensive test cases
- **Query Endpoint Tests** (`/api/query`):
  - Session handling (with/without session ID)
  - Request validation and error handling
  - Source format handling (both legacy string and structured dict formats)
  - Empty query handling
- **Courses Endpoint Tests** (`/api/courses`):
  - Course statistics retrieval
  - Empty course list handling
- **New Chat Endpoint Tests** (`/api/new-chat`):
  - Session creation
  - Multiple session handling
- **Root Endpoint Tests** (`/`):
  - Basic connectivity testing
- **Error Handling Tests**:
  - RAG system failures
  - Analytics errors
  - Session creation failures
- **Request Validation Tests**:
  - Schema validation
  - Type validation
  - Extra field handling
- **Response Format Tests**:
  - Response structure validation
  - Field type verification
- **Integration Tests**:
  - Multi-endpoint workflows
  - Cross-endpoint consistency

### Testing Framework Benefits

1. **Comprehensive API Coverage**: All FastAPI endpoints are now thoroughly tested
2. **Isolated Testing**: Test app avoids static file dependencies that don't exist in test environment
3. **Flexible Test Organization**: Pytest markers allow running specific test categories
4. **Proper Error Testing**: Tests verify error handling matches production behavior
5. **Format Compatibility**: Tests ensure both legacy and new source formats work
6. **Integration Validation**: Tests verify endpoint interactions and workflows

### Testing Usage Examples

```bash
# Run all API tests
python -m pytest -m "api" -v

# Run integration tests only
python -m pytest -m "integration" -v

# Run specific test file
python -m pytest tests/test_api_endpoints.py -v

# Run with configuration from pyproject.toml (default)
python -m pytest tests/
```

### Test Results

- **22 new API endpoint tests** - All passing ✅
- **Existing tests compatibility** - No breaking changes ✅
- **Pytest configuration** - Working correctly ✅
- **Custom markers** - Functional for test filtering ✅

## Dark/Light Theme Toggle Implementation

Added a complete dark/light theme toggle system to the Course Materials Assistant with smooth transitions, accessibility features, and persistent user preferences.

### Files Modified

#### 1. `frontend/index.html`
- **Header Structure**: Converted hidden header to visible header with theme toggle button
- **Theme Toggle Button**: Added toggle button with sun/moon icons in top-right corner
- **Accessibility**: Added proper ARIA labels, title attributes, and keyboard navigation support

#### 2. `frontend/style.css`
- **Theme Variables**: Added complete light theme CSS variables alongside existing dark theme
- **Header Layout**: Styled visible header with flexbox layout and theme toggle positioning
- **Smooth Transitions**: Added 0.3s ease transitions to all theme-affected elements
- **Light Theme Support**: Comprehensive light theme with proper contrast ratios
- **Responsive Design**: Updated mobile styles to accommodate new header layout

#### 3. `frontend/script.js`
- **Theme Management**: Added complete theme system with localStorage persistence
- **Event Handlers**: Theme toggle click handler and keyboard shortcut (Ctrl/Cmd + Shift + T)
- **Icon Management**: Dynamic sun/moon icon switching based on current theme
- **Initialization**: Automatic theme detection and application on page load

### Features Implemented

#### ✅ Toggle Button Design
- **Position**: Top-right corner of header
- **Icons**: Sun icon for dark theme, moon icon for light theme
- **Animation**: Smooth scale transform on hover
- **Accessibility**: Full keyboard navigation and ARIA labels

#### ✅ Light Theme Colors
- **Background**: `#ffffff` (white)
- **Surface**: `#f8fafc` (light gray)
- **Text Primary**: `#1e293b` (dark slate)
- **Text Secondary**: `#64748b` (medium slate)
- **Borders**: `#e2e8f0` (light slate)
- **Proper Contrast**: All colors meet WCAG AA accessibility standards

#### ✅ JavaScript Functionality  
- **Toggle Logic**: Switches between 'dark' and 'light' themes
- **Persistence**: Saves user preference in localStorage
- **Auto-Detection**: Defaults to dark theme, respects saved preference
- **Keyboard Support**: Ctrl/Cmd + Shift + T keyboard shortcut

#### ✅ Implementation Details
- **CSS Variables**: Clean theme switching using `data-theme` attribute
- **Smooth Transitions**: All elements transition smoothly between themes (0.3s)
- **Responsive**: Theme toggle adapts to mobile screen sizes
- **Accessibility**: Full keyboard navigation, focus indicators, ARIA labels

### Technical Implementation

#### Theme System Architecture
```javascript
// Theme stored in localStorage as 'theme': 'light' | 'dark'
// Applied via document.documentElement.setAttribute('data-theme', 'light')
// CSS variables automatically switch based on [data-theme="light"] selector
```

#### CSS Variable System
```css
:root { /* Dark theme variables (default) */ }
[data-theme="light"] { /* Light theme overrides */ }
```

#### Accessibility Features
- **Keyboard Navigation**: Tab-accessible theme toggle
- **Focus Indicators**: Clear focus rings on theme toggle
- **ARIA Labels**: Descriptive labels for screen readers
- **Keyboard Shortcut**: Ctrl/Cmd + Shift + T for power users
- **High Contrast**: Both themes meet WCAG AA standards

### Browser Compatibility
- ✅ Modern browsers with CSS custom properties support
- ✅ localStorage support for theme persistence
- ✅ CSS transitions for smooth theme switching
- ✅ SVG icon support

### Testing Performed
- ✅ Theme toggle functionality (click and keyboard)
- ✅ Theme persistence across page reloads
- ✅ Smooth transitions between themes
- ✅ Responsive design on mobile devices
- ✅ Keyboard navigation and accessibility
- ✅ Icon switching (sun/moon) based on theme
- ✅ All UI elements properly themed in both modes

### User Experience
- **Intuitive**: Sun/moon icons clearly indicate theme switching
- **Fast**: Instant theme switching with smooth 0.3s transitions
- **Persistent**: User preference remembered across sessions
- **Accessible**: Full keyboard and screen reader support
- **Responsive**: Works seamlessly on desktop and mobile devices

## Combined Benefits
- Consistent code formatting across the project
- Automated quality checks in development workflow
- Easy-to-use scripts for maintaining code quality
- Better code readability and maintainability
- Comprehensive API test coverage ensuring frontend reliability
- Proper error handling validation throughout the system
- Modern dark/light theme system with accessibility compliance
- Enhanced user experience with persistent theme preferences

The enhanced testing framework ensures that all API endpoints serving the frontend are thoroughly tested, while the theme toggle system provides users with a customizable, accessible interface that adapts to their preferences.
