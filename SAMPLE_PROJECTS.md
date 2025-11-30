# Sample Projects for Codewise

This directory contains three sample Python projects to test your Codewise code quality analysis tool. Each project is a realistic codebase with multiple files that call each other's functions.

## Project 1: User Management System
**Location:** `../sample_projects/user_management/`

A complete user authentication and session management system.

### Structure:
- `models/user.py` - User model with validation and profile management
- `models/session.py` - Session management and tracking
- `auth.py` - Authentication manager (uses User and Session models)

### Key Features:
- User registration and login
- Email and password validation
- Session creation and validation
- Password change functionality
- Cross-file method calls for testing dependency tracking

### Methods to Analyze:
- `User.validate_email()` - Email validation logic
- `User.validate_password()` - Password strength checking
- `AuthenticationManager.register_user()` - Registration flow with validation
- `AuthenticationManager.login()` - Authentication with session creation
- `AuthenticationManager.get_user_from_session()` - Session-based user retrieval

---

## Project 2: E-commerce Shopping System
**Location:** `../sample_projects/ecommerce/`

A complete e-commerce application with products, shopping carts, and order processing.

### Structure:
- `product.py` - Product model with inventory management
- `cart.py` - Shopping cart and cart item management
- `services/inventory.py` - Inventory management service
- `services/order.py` - Order processing and status tracking

### Key Features:
- Product catalog with ratings and categories
- Shopping cart with discount codes
- Inventory tracking and availability checks
- Order processing workflow
- Complex multi-file interactions

### Methods to Analyze:
- `Product.is_in_stock()` - Inventory check
- `ShoppingCart.add_item()` - Cart operations with validation
- `ShoppingCart.get_total()` - Price calculation with discounts
- `Order.confirm_order()` - Multi-step order workflow
- `InventoryManager.get_low_stock_products()` - Data filtering

---

## Project 3: Data Processing Pipeline
**Location:** `../sample_projects/data_pipeline/`

A flexible data processing pipeline for ETL (Extract, Transform, Load) operations.

### Structure:
- `data_source.py` - Abstract data sources (JSON, CSV)
- `processors/filter_processor.py` - Data filtering
- `processors/transform_processor.py` - Data transformation
- `processors/aggregation_processor.py` - Data aggregation and grouping
- `pipeline.py` - Main pipeline orchestrator

### Key Features:
- Multiple data source types (JSON, CSV)
- Chainable filter operations
- Field transformation (rename, compute, trim, case conversion)
- Data aggregation and grouping
- Caching support
- Progressive processing

### Methods to Analyze:
- `FilterProcessor.process()` - Complex filtering logic
- `TransformProcessor.process()` - Field transformation pipeline
- `AggregationProcessor.group_by()` - Data grouping
- `DataPipeline.execute()` - Full pipeline execution
- `DataPipeline.load_data()` - Data source loading with caching

---

## Testing Your Tool

### Quick Start:
```bash
# Analyze entire user management project
python code_evaluator.py
# Select "Entire Project Mode"
# Choose: ../sample_projects/user_management

# Analyze specific file
# Or select "Single File Mode"
# Choose: ../sample_projects/ecommerce/cart.py
```

### What to Look For:

**User Management Project** - Tests:
- Validation logic complexity
- Error handling
- Cryptographic operations (password hashing)
- State management across files

**E-commerce Project** - Tests:
- Business logic complexity
- Multiple validation rules
- Decimal arithmetic (pricing)
- Enum usage for status tracking

**Data Pipeline Project** - Tests:
- Functional programming patterns (lambda functions)
- Higher-order functions
- Abstract base classes
- Chainable builder pattern

---

## Code Quality Observations

### Good Code Examples:
- `User.validate_email()` - Simple, focused validation
- `FilterProcessor.filter_by_field()` - Clear method with chainable pattern
- `AggregationProcessor.group_by()` - Efficient static method

### Complex Code Examples (for analysis):
- `ShoppingCart.add_item()` - Multiple validation steps
- `DataPipeline.execute()` - Sequential processing pipeline
- `FilterProcessor.filter_by_condition()` - Dynamic operator handling
- `AuthenticationManager.register_user()` - Multi-step validation workflow

---

## Notes

- These projects intentionally contain methods with varying quality levels
- Some methods have good separation of concerns, others could be refactored
- The projects use different Python patterns (OOP, functional, builder pattern)
- No external dependencies required - pure Python standard library usage
- Suitable for testing both "Single File" and "Entire Project" analysis modes
