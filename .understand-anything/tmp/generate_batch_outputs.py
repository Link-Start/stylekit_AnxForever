#!/usr/bin/env python3
"""Read structural extraction results and generate batch output files."""
import json
import os
import sys

OUTPUT_DIR = "/home/anx4758/stylekit/.understand-anything/intermediate"
TMP_DIR = "/home/anx4758/stylekit/.understand-anything/tmp"

def load_input(batch_idx):
    path = os.path.join(TMP_DIR, f"ua-file-analyzer-input-{batch_idx}.json")
    with open(path) as f:
        return json.load(f)

def load_struct(batch_idx):
    path = os.path.join(TMP_DIR, f"ua-file-analyzer-struct-{batch_idx}.json")
    with open(path) as f:
        return json.load(f)

def make_file_node(entry, file_cat="code"):
    """Create a file-level node."""
    path = entry["path"]
    name = os.path.basename(path)
    total_lines = entry.get("totalLines", 0)
    non_empty = entry.get("nonEmptyLines", 0)
    func_count = entry.get("metrics", {}).get("functionCount", 0)
    class_count = entry.get("metrics", {}).get("classCount", 0)
    exp_count = entry.get("metrics", {}).get("exportCount", 0)

    # Determine complexity
    if non_empty < 50 and func_count <= 2:
        complexity = "simple"
    elif non_empty < 200 and func_count <= 8:
        complexity = "moderate"
    else:
        complexity = "complex"

    # Determine node type based on fileCategory and content
    node_type = "file"

    # Determine summary and tags based on the file path and function data
    tags = []
    summary = ""

    # Detect test files
    is_test = "/__tests__/" in path or path.endswith(".test.ts") or path.endswith(".test.tsx") or path.endswith(".spec.ts")
    is_page = "/page.tsx" in path or "/page.tsx" == path
    is_layout = "/layout.tsx" in path or "/layout.tsx" == path
    is_route = "/route.ts" in path and "api/" in path
    is_component = path.startswith("components/")
    is_lib = path.startswith("lib/")

    # Generate summaries based on file path patterns
    if is_test:
        # Determine what it tests
        test_target = path.replace("__tests__/", "").replace("/route.test.ts", "/route.ts").replace(".test.ts", ".ts").replace(".test.tsx", ".tsx")
        # Get the proper test description
        if "/api/admin/" in path:
            summary = f"Unit tests for the admin API route at {path.split('/__tests__/')[0] if '/__tests__/' in path else path}, covering request validation, authorization checks, and response handling."
        elif "/api/favorites/" in path:
            summary = f"Unit tests for favorites API endpoints, covering merge operations, authorization, and request validation."
        elif "/api/styles/" in path:
            summary = f"Unit tests for styles API routes, covering core CRUD operations, rate limiting, and security validation."
        elif "/lib/" in path:
            lib_name = os.path.basename(path).replace(".test.ts", "").replace(".test.tsx", "")
            summary = f"Unit tests for the {lib_name} library module, verifying expected outputs and edge cases."
        else:
            summary = f"Unit tests covering the API route handlers and request validation."
        tags = ["test", "api-handler"]
    elif is_route:
        # Determine API route purpose
        if "admin" in path:
            if "analytics" in path:
                summary = "Admin API route providing analytics dashboard data with content summaries, trends, and usage statistics from Supabase."
            elif "audit" in path:
                summary = "Admin API route for exporting audit events as CSV or fetching paginated audit logs with filtering."
            elif "auth" in path:
                summary = "Admin authentication API route handling password-based login via POST and session logout via DELETE."
            elif "comments" in path:
                summary = "Admin API route for listing and deleting style comments with pagination and filtering."
            elif "ratings" in path:
                summary = "Admin API route for querying and deleting style ratings with distribution breakdowns."
            elif "styles" in path and "/api/admin/" in path:
                summary = "Admin API route for listing all styles with view counts, ratings, and comment metrics."
            elif "submissions" in path:
                chunk = path.split("/submissions")[1] if "/submissions" in path else ""
                if "/register" in chunk:
                    summary = "Admin API route for auto-registering approved style submissions into the codebase."
                elif "/review" in chunk:
                    summary = "Admin API route for reviewing style submissions with approve/reject workflow and audit logging."
                elif "[id]" in chunk:
                    summary = "Admin API route for managing individual style submissions with GET, DELETE, and PATCH operations."
                else:
                    summary = "Admin API route listing style submissions with pagination and status filtering."
            elif "system" in path:
                summary = "Admin API route exposing system information including environment, database, runtime, and audit status."
            elif "user-titles" in path:
                summary = "Admin API route for managing user display titles with PUT create/update and DELETE capabilities."
            elif "users" in path:
                if "content" in path:
                    summary = "Admin API route for managing user-generated content moderation with listing and deletion."
                else:
                    summary = "Admin API route for user management with listing, search, and role/status controls."
            else:
                summary = f"Admin API route at {path} with authorization checks."
        elif "favorites" in path:
            if "merge" in path:
                summary = "API route merging anonymous favorites into user favorites after authentication."
            else:
                summary = "API route managing user favorites with list, add, and remove operations."
        elif "styles" in path:
            if "/comments" in path:
                comment_part = path.split("/comments")[1] if "/comments" in path else ""
                if "[commentId]" in comment_part:
                    summary = "API route for editing and deleting individual comments on style pages."
                else:
                    summary = "API route for creating and listing comments on style pages with pagination."
            elif "/rate" in path:
                summary = "API route for submitting and retrieving ratings on styles with rate limiting."
            elif "/claude-rules" in path:
                summary = "API route returning Claude AI rules configuration for a specific style."
            elif "/cursorrules" in path:
                summary = "API route returning Cursor IDE rules configuration for a specific style."
            elif "/md" in path:
                summary = "API route generating structured markdown documentation for a style including tokens, recipes, and design guidelines."
            elif "/recipes" in path:
                summary = "API route returning style recipes and community components with usage tracking."
            elif "/skill-pack" in path:
                summary = "API route generating downloadable skill packs for a style."
            elif "/tokens" in path:
                summary = "API route returning design tokens for a specific style."
            elif "/versions" in path:
                summary = "API route managing style versioning and retrieving version history."
            elif "[slug]" in path and not any(x in path for x in ["/comments", "/rate", "/claude-rules", "/cursorrules", "/md", "/recipes", "/skill-pack", "/tokens", "/versions"]):
                summary = "Primary API route returning full style data including recipes, accessibility scores, and versioning info."
            else:
                summary = "API route listing all available styles with metadata."
        elif "analytics" in path:
            summary = "Public API route for tracking and retrieving analytics events."
        elif "newsletter" in path:
            summary = "API route for newsletter subscription management with rate limiting."
        elif "accessibility" in path:
            summary = "API route for accessibility scoring and WCAG compliance checks."
        elif "ui-plan/validate" in path:
            summary = "API route validating UI plan schemas against defined archetypes and constraints."
        elif "llms-full.txt" in path:
            summary = "API route generating comprehensive LLM context file including all style data."
        elif "llms.md" in path:
            summary = "API route generating LLM-friendly markdown documentation for styles."
        else:
            summary = f"API route at {path}."

        tags = ["api-handler"]
        if "admin" in path:
            tags.append("admin")
        tags.append("route")

    elif is_component:
        name_base = os.path.basename(path).replace(".tsx", "").replace(".ts", "")

        if "export" in path or "export" in name_base:
            summary = f"Component providing UI for exporting style tokens and configurations in various formats."
            tags = ["component", "export"]
        elif "accessibility" in path:
            summary = f"Component displaying accessibility scores and WCAG compliance details."
            tags = ["component", "accessibility"]
        elif "analytics" in path:
            summary = f"Component for tracking page views and analytics events on the client side."
            tags = ["component", "analytics"]
        elif "animations" in path:
            summary = f"Component showcasing animation styles with code tabs and live previews."
            tags = ["component", "animation"]
        elif "backgrounds" in path:
            summary = f"Component displaying background pattern gallery with preview and code."
            tags = ["component", "background"]
        elif "community" in path:
            summary = f"Component showing community stats and engagement metrics."
            tags = ["component", "community"]
        elif "docs" in path:
            summary = f"Documentation content component for displaying component API reference and usage guides."
            tags = ["component", "documentation"]
        elif "favorite" in path:
            summary = f"Toggle button component for adding/removing styles from user favorites."
            tags = ["component", "favorites"]
        elif "github-star" in path:
            summary = f"Component displaying GitHub star count with link to repository."
            tags = ["component", "github"]
        elif "gradients" in path:
            summary = f"Component displaying gradient style gallery with preview and code."
            tags = ["component", "gradient"]
        elif "home" in path:
            if "content" in name_base:
                summary = "Main home page content component composing sections like featured carousel, style cards, and social proof."
            elif "featured" in name_base:
                summary = "Featured styles carousel component for the home page."
            elif "style-card" in name_base:
                summary = "Individual style card component for the style listing grid."
            elif "trending" in name_base:
                summary = "Trending styles display component for the home page."
            elif "quick-export" in name_base:
                summary = "Quick export panel component on the home page for rapid style downloads."
            elif "reveal" in name_base:
                summary = "Scroll-triggered reveal animation wrapper component."
            elif "social" in name_base:
                summary = "Social proof section showing user count and testimonials."
            elif "built-for" in name_base:
                summary = "Home page section describing what the platform is built for."
            elif "how-it-works" in name_base:
                summary = "Step-by-step guide component explaining how to use StyleKit."
            elif "cta" in name_base:
                summary = "Call-to-action banner component for the home page."
            elif "thank-you" in name_base:
                summary = "Thank you modal component shown after user actions."
            else:
                summary = f"Home page component: {name_base}."
            tags = ["component", "home"]
        elif "i18n" in path:
            summary = "Internationalization component managing HTML lang attribute updates."
            tags = ["component", "i18n"]
        elif "layout" in path:
            summary = "Client-side scripts provider component injecting analytics and interaction trackers."
            tags = ["component", "layout"]
        elif "newsletter" in path:
            summary = "Newsletter signup form component with submission handling."
            tags = ["component", "newsletter"]
        elif "providers" in path:
            summary = "Root client providers wrapper composing theme, i18n, favorites, and analytics context providers."
            tags = ["component", "provider"]
        elif "shadows" in path:
            summary = "Component displaying shadow effect gallery with preview and code."
            tags = ["component", "shadows"]
        elif "style-preview" in path:
            if "ai-implementation" in name_base:
                summary = "AI implementation panel generating code snippets for style components."
            elif "code-block" in name_base:
                summary = "Syntax-highlighted code block component for style previews."
            elif "color-palette" in name_base:
                summary = "Color palette display component showing accent, surface, and text colors."
            elif "component-preview" in name_base:
                summary = "Live component preview showcasing how a style renders UI elements."
            elif "example-prompts" in name_base:
                summary = "Example AI prompt suggestions component for style usage."
            elif "prompt-pair" in name_base:
                summary = "Prompt pair exporter component for sharing AI prompt configurations."
            elif "quick-start" in name_base:
                summary = "Quick start guide panel for getting started with a style."
            elif "rules-exporter" in name_base:
                summary = "Component for exporting AI rules configuration for a style."
            elif "style-cover" in name_base:
                summary = "Style cover preview image component with fallback."
            elif "style-pack-export" in name_base:
                summary = "Style pack export component for downloading complete style packages."
            elif "switcher" in name_base:
                summary = "Style preview mode switcher between different rendering options."
            else:
                summary = f"Style preview component: {name_base}."
            tags = ["component", "style-preview"]
        elif "styles" in path:
            if "style-rating" in name_base:
                summary = "Star rating component for user-submitted style ratings."
            elif "version-badge" in name_base:
                summary = "Version badge component displaying style version number."
            elif "styles-content" in name_base:
                summary = "Main styles listing page content with filter, sort, and grid display."
            else:
                summary = f"Styles-related component: {name_base}."
            tags = ["component", "styles"]
        elif "support" in path:
            summary = "Support page content component with sponsorship and thank-you display."
            tags = ["component", "support"]
        elif "templates" in path:
            summary = "Template filter component for filtering available design templates."
            tags = ["component", "templates"]
        elif "theme-provider" in path:
            summary = "Theme context provider component enabling light/dark theme switching."
            tags = ["component", "theme"]
        elif "typography" in path:
            summary = "Typography style showcase component displaying font and text styles."
            tags = ["component", "typography"]
        elif "ui/" in path:
            if "alert" in path:
                summary = "Alert UI component barrel export for the alert primitive."
            elif "button" in path:
                summary = "Button UI component barrel export for the button primitive."
            elif "card" in path:
                summary = "Card UI component barrel export for the card primitive."
            elif "checkbox" in path:
                summary = "Checkbox UI component barrel export."
            elif "collapsible-section" in name_base:
                summary = "Collapsible section wrapper component for expandable content areas."
            elif "command-palette" in name_base:
                summary = "Command palette UI component for keyboard-driven navigation and search."
            elif "drawer" in path:
                summary = "Drawer UI component barrel export for slide-out panels."
            elif "input-otp" in path:
                summary = "OTP input UI component barrel export."
            elif "input" in path:
                summary = "Input UI component barrel export for text input primitive."
            elif "lazy-section" in name_base:
                summary = "Lazy-loading section component for deferred rendering of content areas."
            elif "list" in path:
                summary = "List UI component barrel export."
            elif "loading" in path:
                summary = "Loading spinner UI component barrel export."
            elif "modal" in path:
                summary = "Modal dialog UI component barrel export."
            elif "pagination" in path:
                summary = "Pagination UI component for page navigation controls."
            elif "popover" in path:
                summary = "Popover UI component barrel export."
            elif "progress" in path:
                summary = "Progress bar UI component barrel export."
            elif "radio" in path:
                summary = "Radio button UI component barrel export."
            else:
                summary = f"UI primitive component: {name_base}."
            tags = ["component", "ui"]
        elif "scroll-back-button" in name_base:
            summary = "Scroll-to-top button component for navigation convenience."
            tags = ["component", "navigation"]
        elif "page-transition" in name_base:
            summary = "Page transition animation wrapper component."
            tags = ["component", "animation"]
        elif "pointer-interactions" in path:
            summary = "Pointer interaction barrel export for cursor effects."
            tags = ["component", "interaction"]
        else:
            summary = f"{name_base} component."
            tags = ["component"]

        if is_test:
            tags.append("test")

    elif is_lib:
        lib_name = path.replace("lib/", "").replace(".ts", "").replace("/index", "").replace(".tsx", "")

        if "accessibility" in path:
            if "scorer" in lib_name:
                summary = "Accessibility scoring engine evaluating color contrast ratios and readability metrics for design styles."
                tags = ["accessibility", "utility", "scoring"]
            elif "wcag" in lib_name:
                summary = "WCAG compliance utility library with color conversion, luminance calculation, and contrast ratio evaluation functions."
                tags = ["accessibility", "wcag", "utility"]
            else:
                summary = "Accessibility barrel export module."
                tags = ["accessibility", "barrel"]
        elif "admin" in path:
            if "audit-csv" in lib_name:
                summary = "Admin audit CSV export utility formatting audit events into downloadable CSV format."
            elif "audit-log" in lib_name:
                summary = "Admin audit logging service recording administrative actions to Supabase with event filtering and pagination."
            else:
                summary = f"Admin utility: {lib_name}."
            tags = ["admin", "utility"]
        elif "auth" in path:
            if "admin-api" in lib_name:
                summary = "Admin API authentication middleware verifying admin session cookies and enforcing access control."
            elif "admin-policy" in lib_name:
                summary = "Admin policy definitions for authorization rules and permission checks."
            elif "admin-session" in lib_name:
                summary = "Admin session management service handling cookie-based session creation, verification, and configuration."
            elif "supabase-server" in lib_name:
                summary = "Supabase server-side authentication client for managing user sessions."
            elif "user-title-policy" in lib_name:
                summary = "User display title policy service with validation, normalization, and database operations."
            else:
                summary = f"Auth module: {lib_name}."
            tags = ["auth", "utility"]
        elif "analytics" in path:
            if "/index" in path or path.endswith("analytics/index.ts"):
                summary = "Analytics barrel export providing tracking functions for style usage, trends, and popular combinations."
                tags = ["analytics", "barrel"]
            else:
                summary = "Analytics module: {lib_name}."
                tags = ["analytics"]
        elif "archetypes" in path:
            if "types" in lib_name:
                summary = "Type definitions and layout class utilities for design archetypes including page structure options."
            elif "index" in lib_name:
                summary = "Archetype barrel export with query functions for filtering and searching archetypes by category, tag, or style."
            else:
                category_name = lib_name.split("/")[-1].replace(".ts", "")
                summary = f"Design archetype definitions for {category_name} page layouts with configurable component presets."
            tags = ["archetypes", "data-model"]
        elif "export" in path:
            if "codesandbox" in lib_name:
                summary = "CodeSandbox export utility building file structures and opening sandboxes for style previews."
            elif "figma-tokens" in lib_name:
                summary = "Figma token export service generating Design Tokens format, Style Dictionary, and CSS variable outputs."
            elif "ide-configs" in lib_name:
                summary = "IDE configuration generator producing Claude/Cursor AI rules files for design consistency."
            elif "llms-full" in lib_name:
                summary = "LLM context file generator producing comprehensive markdown including all styles, archetypes, and recipes."
            elif "shadcn-theme" in lib_name:
                summary = "shadcn/ui theme export converter transforming style tokens into shadcn CSS variable format."
            elif "skill-pack" in lib_name:
                summary = "Skill pack generator producing downloadable AI assistant skill packages for each style."
            elif "stackblitz" in lib_name:
                summary = "StackBlitz export utility preparing style previews for online IDE sandboxes."
            elif "style-pack" in lib_name:
                summary = "Style pack assembler combining multiple export formats into downloadable ZIP archives."
            elif "tailwind-preset" in lib_name:
                summary = "Tailwind CSS preset generator converting style tokens into Tailwind-compatible configuration."
            else:
                summary = f"Export module: {lib_name}."
            tags = ["export", "utility"]
        elif "newsletter" in path:
            summary = "Newsletter subscription service handling email signups and dispatch."
            tags = ["newsletter", "utility"]
        elif "og" in path:
            summary = "Open Graph image generation utilities for creating dynamic social share previews."
            tags = ["og", "utility"]
        elif "recipes" in path:
            if "/index" in path or path.endswith("recipes/index.ts"):
                summary = "Recipes barrel export providing design recipe definitions for common UI patterns."
                tags = ["recipes", "barrel"]
            else:
                summary = f"Recipes module: {lib_name}."
            tags = ["recipes"]
        elif "schema" in path:
            if "ui-plan" in lib_name:
                summary = "UI plan schema definitions with Zod validation for generating UI from design specifications."
            elif "validator" in lib_name:
                summary = "UI plan schema validator ensuring generated plans conform to style constraints and archetype rules."
            else:
                summary = f"Schema module: {lib_name}."
            tags = ["schema", "validation"]
        elif "security" in path:
            if "json-body" in lib_name:
                summary = "JSON body parser with size limits to prevent request body denial-of-service attacks."
            elif "rate-limit" in lib_name:
                summary = "Rate limiting middleware using an in-memory sliding window to prevent API abuse."
            elif "request-origin" in lib_name:
                summary = "Request origin verification utility checking trusted sources for sensitive operations."
            else:
                summary = f"Security module: {lib_name}."
            tags = ["security", "middleware"]
        elif "styles" in path:
            if "community-runtime" in lib_name:
                summary = "Community style runtime service managing dynamic style registration, listing, and community content."
            elif "enhanced-rules" in lib_name:
                summary = "Enhanced style rules generator producing detailed design constraints and token mappings."
            elif "index" in lib_name:
                summary = "Style registry barrel export listing all design styles with their metadata."
            elif "rule-normalizer" in lib_name:
                summary = "Style rule normalizer transforming raw style rules into structured format for consistency."
            elif "style-diff" in lib_name:
                summary = "Style diff utility comparing two style configurations and reporting differences."
            elif "token-diff" in lib_name:
                summary = "Token diff utility identifying changes between two sets of design tokens."
            elif "tokens-registry" in lib_name:
                summary = "Tokens registry barrel export providing access to all design token data."
            elif "tokens" in lib_name:
                summary = "Design tokens data containing color palettes, spacing, typography, and other design primitives."
            else:
                summary = f"Styles module: {lib_name}."
            tags = ["styles", "utility"]
        elif "submit" in path:
            if "auto-register" in lib_name:
                summary = "Style auto-registration service generating code scaffolding and registering new styles into the codebase."
            elif "reviewer-supabase" in lib_name:
                summary = "Supabase-backed reviewer service handling style submission review, approval, and rejection workflows."
            elif "reviewer" in lib_name:
                summary = "Core style submission reviewer with logic for evaluating style quality and completeness."
            else:
                summary = f"Submission module: {lib_name}."
            tags = ["submission", "utility"]
        elif "supabase" in path:
            summary = "Supabase server client factory creating authenticated database connections."
            tags = ["database", "utility"]
        elif "versioning" in path:
            if "index" in lib_name:
                summary = "Versioning barrel export for style version management."
            elif "registry" in lib_name:
                summary = "Version registry service maintaining version history records."
            elif "types" in lib_name:
                summary = "Versioning type definitions for style version data structures."
            elif "version-data" in lib_name:
                summary = "Version data service handling version creation, storage, and retrieval for style iteration tracking."
            else:
                summary = f"Versioning module: {lib_name}."
            tags = ["versioning", "utility"]
        elif lib_name == "proxy":
            summary = "Middleware proxy handling request routing, i18n redirection, and admin session verification."
            tags = ["middleware", "routing"]
        else:
            summary = f"Library module: {lib_name}."
            tags = ["utility"]

        if is_test:
            tags.append("test")

    elif is_page:
        if "admin-login" in path:
            if "_content" in path:
                summary = "Admin login form component with password submission, error handling, and redirect after authentication."
            else:
                summary = "Admin login page with session verification that redirects authenticated users to the admin dashboard."
            tags = ["page", "admin", "auth"]
        elif "preview" in path:
            summary = "Style preview page rendering live component previews with customizations."
            tags = ["page", "preview"]
        elif "templates" in path:
            summary = "Templates layout page wrapping template content with analytics tracking."
            tags = ["page", "layout"]
        elif "login" in path and "_content" in path:
            summary = "User login form component supporting email/password authentication."
            tags = ["page", "auth"]
        elif "error" in path:
            summary = "Application error boundary page displaying user-friendly error messages."
            tags = ["page", "error"]
        elif "not-found" in path:
            summary = "Custom 404 not-found page with navigation back to home."
            tags = ["page", "error"]
        elif "opengraph-image" in path:
            summary = "Dynamic Open Graph image generator for social media sharing previews."
            tags = ["og", "image"]
        elif "showcase" in path:
            if "_content" in path:
                summary = "Style showcase page content displaying component variations and demos."
            else:
                summary = "Style showcase page route with dynamic rendering and metadata."
            tags = ["page", "showcase"]
        elif "[slug]" in path and "_content" in path:
            summary = "Style detail page content with full style information, previews, ratings, and community features."
            tags = ["page", "style-detail"]
        elif "components" in path and "_shared" in path:
            summary = "Shared UI components gallery page with common section rendering utilities."
            tags = ["page", "components"]
        else:
            summary = f"Page: {name}."
            tags = ["page"]
    else:
        summary = f"{name}"
        tags = []

    # Determine node type
    if is_page and not is_route:
        node_type = "file"
    else:
        node_type = "file"

    # Build node
    node = {
        "id": f"file:{path}",
        "type": node_type,
        "name": name,
        "filePath": path,
        "summary": summary,
        "tags": tags[:5] if tags else ["utility"],
        "complexity": complexity
    }

    # Add language notes for barrel files
    if len(entry.get("exports", [])) > 5 and func_count == 0:
        node["languageNotes"] = "Barrel file re-exporting multiple modules."

    return node

def make_func_node(entry, func, path):
    """Create a function node if it meets significance criteria."""
    name = func["name"]
    start = func["startLine"]
    end = func["endLine"]
    params = func.get("params", [])
    lines = end - start + 1

    is_exported = any(e["name"] == name for e in entry.get("exports", []))

    # Significance filter: 10+ lines OR exported
    if lines < 10 and not is_exported:
        return None

    # Skip trivial 1-liners
    if lines <= 2 and not is_exported:
        return None

    # Default tags
    tags = ["function"]

    # Detect handler functions
    if name in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        tags = ["api-handler", "route-handler"]
    elif name.startswith("use"):
        tags = ["hook", "react"]
    elif name.startswith("handle"):
        tags = ["event-handler"]
    elif name.startswith("get"):
        tags = ["getter", "utility"]

    # Complexity for function
    if lines < 20:
        complexity = "simple"
    elif lines < 50:
        complexity = "moderate"
    else:
        complexity = "complex"

    summary = f"Function {name}"
    if name in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        summary = f"HTTP {name} handler"
        if "admin" in path:
            summary += " for admin API with authentication checks."
        else:
            summary += " returning JSON response."
    elif name.startswith("handle"):
        summary = f"Event handler for {name.replace('handle', '').lower()} interactions."
    else:
        summary = f"{name} function with {len(params)} parameters."

    node = {
        "id": f"function:{path}:{name}",
        "type": "function",
        "name": name,
        "filePath": path,
        "lineRange": [start, end],
        "summary": summary,
        "tags": tags,
        "complexity": complexity
    }
    return node

def process_batch(batch_idx):
    """Process a single batch."""
    inp = load_input(batch_idx)
    struct = load_struct(batch_idx)

    project_root = inp["projectRoot"]
    batch_files = inp["batchFiles"]
    batch_imports = inp["batchImportData"]

    # Build path lookup
    file_lookup = {}
    for bf in batch_files:
        file_lookup[bf["path"]] = bf

    # Build struct lookup
    struct_lookup = {}
    for r in struct.get("results", []):
        struct_lookup[r["path"]] = r

    nodes = []
    edges = []
    added_node_ids = set()

    # Process each file
    for bf in batch_files:
        path = bf["path"]
        entry = struct_lookup.get(path, {})

        # Create file node
        file_node = make_file_node(entry if entry else bf, bf.get("fileCategory", "code"))
        nodes.append(file_node)
        added_node_ids.add(file_node["id"])

        file_id = file_node["id"]

        # Create function/class nodes
        for func in entry.get("functions", []):
            func_node = make_func_node(entry, func, path)
            if func_node:
                nodes.append(func_node)
                added_node_ids.add(func_node["id"])
                # Add contains edge
                edges.append({
                    "source": file_id,
                    "target": func_node["id"],
                    "type": "contains",
                    "direction": "forward",
                    "weight": 1.0
                })
                # Add exports edge if exported
                if any(e["name"] == func["name"] and e.get("isDefault", False) == False for e in entry.get("exports", [])):
                    edges.append({
                        "source": file_id,
                        "target": func_node["id"],
                        "type": "exports",
                        "direction": "forward",
                        "weight": 0.8
                    })
                # Check if it's default export
                if any(e["name"] == func["name"] and e.get("isDefault", False) == True for e in entry.get("exports", [])):
                    edges.append({
                        "source": file_id,
                        "target": func_node["id"],
                        "type": "exports",
                        "direction": "forward",
                        "weight": 0.8
                    })

        # Add import edges from batchImportData
        if path in batch_imports:
            for import_path in batch_imports[path]:
                target_id = f"file:{import_path}"
                edges.append({
                    "source": file_id,
                    "target": target_id,
                    "type": "imports",
                    "direction": "forward",
                    "weight": 0.7
                })

        # Add tested_by edges for test files
        if "/__tests__/" in path or path.startswith("tests/"):
            # Find the production file this tests
            prod_path = path.replace("/__tests__/", "/").replace("/route.test.ts", "/route.ts").replace(".test.ts", ".ts").replace(".test.tsx", ".tsx")
            prod_path = prod_path.replace("tests/unit/", "")

            # Check if any imported path is in our batch
            if path in batch_imports:
                for import_path in batch_imports[path]:
                    if import_path.startswith("app/") or import_path.startswith("lib/") or import_path.startswith("components/"):
                        prod_id = f"file:{import_path}"
                        edges.append({
                            "source": prod_id,
                            "target": file_id,
                            "type": "tested_by",
                            "direction": "forward",
                            "weight": 0.5
                        })

        # Add depends_on for api routes
        if "app/api/" in path and path in batch_imports:
            for import_path in batch_imports[path]:
                if import_path.startswith("lib/"):
                    target_id = f"file:{import_path}"
                    # Skip if already an import edge
                    pass

    # Verify import edge counts
    expected_imports = sum(len(v) for k, v in batch_imports.items() if k in file_lookup)
    actual_imports = sum(1 for e in edges if e["type"] == "imports")

    if expected_imports != actual_imports:
        print(f"Batch {batch_idx}: Expected {expected_imports} import edges, got {actual_imports}", file=sys.stderr)

    # Deduplicate edges
    seen_edges = set()
    deduped_edges = []
    for e in edges:
        key = (e["source"], e["target"], e["type"])
        if key not in seen_edges:
            seen_edges.add(key)
            deduped_edges.append(e)
    edges = deduped_edges

    return nodes, edges


def main():
    for batch_idx in [1, 2, 3, 4, 5, 6, 7]:
        print(f"Processing batch {batch_idx}...")
        try:
            nodes, edges = process_batch(batch_idx)

            # Check if we need multipart output
            node_count = len(nodes)
            edge_count = len(edges)

            if node_count <= 60 and edge_count <= 120:
                output = {"nodes": nodes, "edges": edges}
                out_path = os.path.join(OUTPUT_DIR, f"batch-{batch_idx}.json")
                with open(out_path, "w") as f:
                    json.dump(output, f, indent=2)
                print(f"  Batch {batch_idx}: {node_count} nodes, {edge_count} edges -> batch-{batch_idx}.json")
            else:
                # Split into parts
                parts = max(1, -(-max(node_count, edge_count) // 60))  # ceil division
                # Actually use the formula: parts = ceil(max(nodeCount / 60, edgeCount / 120))
                parts = max(1, int(-(-max(node_count / 60, edge_count / 120))))

                # Sort files by path
                file_nodes = [n for n in nodes if n["type"] == "file"]
                file_nodes.sort(key=lambda n: n["filePath"])

                # Chunk files
                files_per_part = max(1, -(-len(file_nodes) // parts))
                for part_idx in range(parts):
                    start = part_idx * files_per_part
                    end = min(start + files_per_part, len(file_nodes))
                    part_file_paths = set(fn["filePath"] for fn in file_nodes[start:end])

                    part_nodes = []
                    part_node_ids = set()

                    # Include file nodes in this chunk
                    for fn in file_nodes[start:end]:
                        part_nodes.append(fn)
                        part_node_ids.add(fn["id"])

                    # Include function/class nodes belonging to these files
                    for n in nodes:
                        if n["type"] in ("function",):
                            if n.get("filePath") in part_file_paths:
                                part_nodes.append(n)
                                part_node_ids.add(n["id"])

                    # Include non-file nodes if their filePath is in this chunk
                    for n in nodes:
                        if n["type"] not in ("file", "function"):
                            if n.get("filePath") in part_file_paths:
                                part_nodes.append(n)
                                part_node_ids.add(n["id"])

                    # Include edges where source is in this part
                    part_edges = []
                    for e in edges:
                        if e["source"] in part_node_ids or e["target"] in part_node_ids:
                            part_edges.append(e)

                    output = {"nodes": part_nodes, "edges": part_edges}
                    out_path = os.path.join(OUTPUT_DIR, f"batch-{batch_idx}-part-{part_idx + 1}.json")
                    with open(out_path, "w") as f:
                        json.dump(output, f, indent=2)
                    print(f"  Batch {batch_idx} part {part_idx + 1}: {len(part_nodes)} nodes, {len(part_edges)} edges")

        except Exception as e:
            print(f"Error processing batch {batch_idx}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
