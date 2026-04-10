# Changelog

All notable changes to the FlavorVault project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-15

### Added

#### User Authentication
- User registration with email validation and secure password hashing
- User login with JWT-based authentication and token refresh
- User profile management with editable display name, bio, and avatar
- Password reset functionality via email
- Role-based access control with user and admin roles

#### Recipe CRUD
- Create new recipes with title, description, ingredients, instructions, prep time, cook time, and servings
- Read recipe details with full ingredient lists and step-by-step instructions
- Update existing recipes with ownership validation
- Delete recipes with cascading removal of associated data
- Image upload support for recipe photos
- Pagination for recipe listing endpoints

#### Tag System
- Create and manage tags for recipe categorization
- Assign multiple tags to recipes via many-to-many relationships
- Browse recipes by tag with filtered listing endpoints
- Tag-based navigation for discovering related recipes

#### Search and Filtering
- Full-text search across recipe titles and descriptions
- Filter recipes by tags, prep time, cook time, and difficulty level
- Sort recipes by date created, rating, and popularity
- Combined search and filter support for advanced queries

#### Reviews and Ratings
- Submit reviews with star ratings (1-5) and text comments for recipes
- Edit and delete own reviews
- Aggregate rating calculation per recipe with average score and review count
- Prevent duplicate reviews from the same user on a single recipe

#### Favorites
- Add recipes to personal favorites collection
- Remove recipes from favorites
- View all favorited recipes in a dedicated listing
- Favorite count tracking per recipe

#### Admin Dashboard
- Admin-only endpoints for user management
- Ability to moderate and remove inappropriate recipes and reviews
- Overview statistics for total users, recipes, reviews, and tags
- User role promotion and demotion capabilities

#### Responsive Design
- Mobile-first responsive layout for all pages
- Tailwind CSS utility-based styling throughout the application
- Accessible navigation with collapsible mobile menu
- Optimized card layouts for recipe browsing on all screen sizes

#### Infrastructure
- FastAPI backend with async SQLAlchemy and SQLite/PostgreSQL support
- Pydantic v2 schemas for request and response validation
- Alembic database migrations setup
- CORS middleware configuration for frontend integration
- Structured logging with Python logging module
- Comprehensive test suite using pytest and httpx