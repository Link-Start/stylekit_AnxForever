#!/usr/bin/env python3
"""Generate batch output files for batches 15-21 with improved analysis."""

import json
import os
import re

PROJECT_ROOT = "/home/anx4758/stylekit"
TMP_DIR = os.path.join(PROJECT_ROOT, ".understand-anything", "tmp")
OUT_DIR = os.path.join(PROJECT_ROOT, ".understand-anything", "intermediate")

def load_json(path):
    with open(path) as f:
        return json.load(f)

def get_file_name(path):
    return path.split("/")[-1]

def guess_function_lines(func_name, path, non_empty_lines):
    """For legacy animation files, examine the file to find export definitions."""
    fpath = os.path.join(PROJECT_ROOT, path)
    if not os.path.exists(fpath):
        return None
    try:
        with open(fpath) as f:
            content = f.read()
        # Find the function/object definition
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith("export const") or line.strip().startswith("export function"):
                start = i + 1
                # Find end - look for empty line after a closing brace
                brace_depth = 0
                in_obj = False
                for j in range(i, min(i + 500, len(lines))):
                    cl = lines[j]
                    brace_depth += cl.count("{") - cl.count("}")
                    if brace_depth <= 0 and "}" in cl and j > i:
                        return [start, j + 1]
                return [start, min(i + 50, len(lines))]
        return None
    except:
        return None

def make_file_node(result, bf):
    """Create a file node with better summaries."""
    path = result["path"]
    non_empty = result.get("nonEmptyLines", result.get("totalLines", 0))
    total_lines = result.get("totalLines", 0)
    func_count = result.get("metrics", {}).get("functionCount", 0)
    class_count = result.get("metrics", {}).get("classCount", 0)
    export_count = result.get("metrics", {}).get("exportCount", 0)
    import_count = result.get("metrics", {}).get("importCount", 0)

    fname = get_file_name(path)

    # Complexity
    if non_empty < 50 and func_count <= 1:
        complexity = "simple"
    elif non_empty < 200 or func_count <= 5:
        complexity = "moderate"
    else:
        complexity = "complex"

    # Tags
    tags = []
    summary = ""

    # Determine route context for app files
    route_parts = []
    if path.startswith("app/") and ("page.tsx" in fname or "page.ts" in fname):
        route = path.replace("app/", "").replace("/page.tsx", "").replace("/page.ts", "")
        route_parts = [p for p in route.split("/") if p]
    elif path.startswith("app/") and "_content.tsx" in fname:
        route_parts = [p for p in path.replace("app/", "").replace("/_content.tsx", "").split("/") if p]
    elif path.startswith("app/") and "-client.tsx" in fname:
        route_parts = [p for p in path.replace("app/", "").replace("/page.tsx", "").replace("/page.ts", "").split("/") if p]

    has_locale = "[locale]" in path

    # App internal route files (_content, etc)
    if path.startswith("app/") and ("_content.tsx" in path or "_content.ts" in path):
        tags.append("content-component")
        domain = path.split("/")[1]
        tags.append(domain)
        summary = f"Content component for {domain} detail pages with i18n support and structured data rendering."
    # App opengraph images
    elif "opengraph-image.tsx" in path:
        tags.append("og-image")
        tags.append("seo")
        summary = "OpenGraph image generation component for social media preview cards."
    # App client components (non-page)
    elif path.startswith("app/") and ("-client.tsx" in fname or "-client.ts" in fname):
        tags.append("client-component")
        domain = path.split("/")[-2]
        tags.append(domain)
        summary = f"Client-side component for the {domain} section with interactive functionality."
    # App routes (non-page)
    elif path.startswith("app/") and "route.ts" in fname:
        tags.append("api-route")
        route_name = path.split("/")[-2] if path.count("/") > 2 else "api"
        tags.append(route_name.replace(".xml", ""))
        summary = f"API route handler serving {route_name} dynamic content."
    # App sitemap / robots
    elif path == "app/sitemap.ts":
        tags.extend(["seo", "sitemap"])
        summary = "Sitemap generator producing localized URL entries for all content types across locales."
    elif path == "app/robots.ts":
        tags.extend(["seo", "robots"])
        summary = "Robots.txt generator defining crawl rules and sitemap reference."
    # Locale pages
    elif has_locale and ("page.tsx" in fname or "page.ts" in fname):
        tags.append("i18n")
        tags.append("page")
        page_name = path.replace("app/[locale]/", "").replace("/page.tsx", "").replace("/page.ts", "")
        if page_name:
            page_tag = page_name.replace("/", "-").replace("[slug]", "detail")
            tags.append(page_tag)
            summary = f"Localized route page for {page_name} with locale-aware metadata generation."
        else:
            summary = "Localized root page with locale-aware metadata generation."
    # Locale layout
    elif has_locale and "layout" in fname:
        tags.extend(["layout", "i18n"])
        summary = "Locale layout component providing i18n context and locale validation."
    # Regular app content pages (page.tsx)
    elif path.startswith("app/") and ("page.tsx" in fname or "page.ts" in fname):
        tags.append("page")
        for rp in route_parts:
            if rp and rp != "[slug]":
                tags.append(rp)
                break

        page_key = "/".join(route_parts) if route_parts else "home"
        if page_key == "":
            summary = "Home page server component rendering the landing content with stats and featured sections."
        elif page_key == "about":
            summary = "About page rendering company/team information with i18n support."
        elif page_key == "contact":
            summary = "Contact page with support information and contact methods."
        elif page_key == "privacy":
            summary = "Privacy policy page with legal text and compliance information."
        elif page_key == "terms":
            summary = "Terms of service page with legal text and usage conditions."
        elif page_key == "login":
            summary = "Login page providing authentication entry point."
        elif page_key == "docs":
            summary = "Documentation page rendering project guides and references."
        elif page_key in ["backgrounds", "gradients", "shadows", "typography"]:
            tags.append("gallery")
            summary = f"Gallery page for {page_key} showcasing available visual resources with layout components."
        elif page_key == "prompts":
            summary = "Prompts overview page categorizing and listing all prompt topics with descriptions."
        elif page_key in ["ui-prompts", "dark-mode-ui-prompts", "dashboard-prompts", "landing-page-prompts", "tailwind-ui-prompts"]:
            tags.append("prompts")
            summary = f"Prompt topic page for {page_key.replace('-', ' ')} rendering content with related styles and JSON-LD."
        elif page_key == "component-patterns":
            summary = "Component patterns showcase page displaying UI design patterns with live previews."
        elif page_key == "guide":
            summary = "Quick start guide page with step-by-step instructions for using the platform."
        elif page_key == "guides":
            summary = "Style guides listing page displaying all guides as cards with descriptions."
        elif page_key in ["mouse-interactions", "html-in-canvas"]:
            tags.append("demo")
            summary = f"Interactive demo page for {page_key.replace('-', ' ')} showcasing experimental browser features."
        elif page_key.startswith("animations"):
            tags.append("animation")
            summary = f"Animations page rendering all animation entries with meta information."
        elif page_key.startswith("blog"):
            tags.append("blog")
            summary = "Blog page fetching and rendering all published blog posts."
        elif page_key.startswith("changelog"):
            tags.append("changelog")
            summary = "Changelog page rendering version history entries."
        elif page_key.startswith("styles"):
            if "[slug]" in path or "slug" in str(route_parts):
                tags.append("detail")
                summary = "Style detail page with versioning, accessibility scoring, compatibility, and localized content."
            else:
                summary = "Styles listing page with metadata, catalog, and JSON-LD for SEO."
        elif page_key.startswith("recipes"):
            summary = "Recipes page displaying design recipes with filtering and JSON-LD."
        elif page_key.startswith("templates"):
            tags.append("templates")
            summary = "Templates catalog page listing all available design templates with filtering."
        elif page_key.startswith("components"):
            summary = "UI components showcase page with interactive prop controls and preview sections."
        else:
            summary = f"Page component for the /{page_key} route with server-rendered content."
    # App layouts (non-locale)
    elif "layout.tsx" in fname or "layout" in fname:
        tags.append("layout")
        if path == "app/layout.tsx":
            summary = "Root layout defining HTML structure, viewport, metadata, fonts, and client-side providers."
        else:
            summary = f"Layout component for {path.split('/')[1]} section."
    # Loading / error / etc
    elif "loading.tsx" in fname:
        tags.append("loading")
        tags.append("ui")
        summary = "Loading skeleton component for Suspense fallback during page transitions."
    # App routes
    elif "route.ts" in path:
        tags.append("api-route")
        route_name = path.split("/")[-2] if "/" in path else "api"
        tags.append(route_name.replace(".xml", ""))
        summary = f"API route handler serving {route_name} dynamic content."
    # App sub-modules (non-page index.ts)
    elif path.startswith("app/") and not fname.startswith("page"):
        tags.append("module")
        module_name = path.split("/")[2] if len(path.split("/")) > 2 else "app"
        tags.append(module_name)
        sub = fname.replace(".tsx", "").replace(".ts", "")
        if sub == "index" and "sections" in path:
            summary = "Barrel file re-exporting all UI component section modules for the components showcase page."
        else:
            summary = f"App sub-module providing {sub} functionality."
    # Components
    elif path.startswith("components/"):
        tags.append("component")
        comp_type = path.split("/")[1]
        tags.append(comp_type)
        if comp_type == "ui":
            comp_name = path.split("/")[2]
            tags.append(comp_name)
            summary = f"Barrel file re-exporting the {comp_name} UI primitive module."
        elif comp_type == "layout":
            comp_name = fname.replace(".tsx", "").replace(".ts", "")
            if "header" in comp_name:
                summary = "Site header component with navigation links, language switcher, and user menu."
            elif "footer" in comp_name:
                summary = "Site footer component with links and newsletter signup."
            elif "menu" in comp_name:
                summary = "Component rendering the user account dropdown menu."
            elif "mobile" in comp_name:
                summary = "Mobile bottom navigation bar for touch-friendly site navigation."
            elif "banner" in comp_name:
                summary = "Announcement banner component displaying site-wide notices."
            else:
                summary = f"Layout component providing {comp_name.replace('-', ' ')}."
        elif comp_type == "animations":
            comp_name = fname.replace(".tsx", "").replace(".ts", "")
            if "preview" in comp_name:
                summary = f"Full-page animation preview component with interactive controls and sandbox."
            elif "card" in comp_name:
                summary = "Animation card component displaying animation metadata and mini-preview."
            elif "content" in comp_name:
                summary = "Animation listing content component with filtering and category display."
            elif "mini" in comp_name:
                summary = "Mini animation preview component for inline display in cards and lists."
            elif "vocabulary" in comp_name:
                vocab_part = path.split("/")[-1].replace(".tsx", "")
                summary = f"Animation vocabulary {vocab_part} component displaying animation term definitions."
            elif "sandbox" in comp_name:
                summary = "Animation sandbox component with preview rendering and code snippet display."
            else:
                summary = f"Animation component providing {comp_name} functionality."
        elif comp_type in ["blog", "recipes", "seo", "style-preview", "templates"]:
            comp_name = fname.replace(".tsx", "").replace(".ts", "")
            if "card" in comp_name:
                summary = f"Card component rendering a single {comp_type} item with visual preview."
            elif "showcase" in comp_name:
                summary = f"Showcase component displaying a grid of {comp_type} items."
            elif "preview" in comp_name:
                summary = f"Preview component rendering {comp_type} visual examples."
            else:
                summary = f"Component for the {comp_type} section."
        else:
            summary = f"Component providing {comp_type} functionality."
    # Lib files
    elif path.startswith("lib/"):
        tags.append("utility")
        if "/_legacy/" in path:
            tags.append("legacy")
            anim_name = fname.replace(".ts", "")
            summary = f"Legacy animation definition for {anim_name} implementing CSS keyframe-based motion effects."
        elif "preview" in fname.lower() or "/preview" in path:
            tags.append("preview")
            anim_name = path.split("/")[-2] if "/" in path else ""
            summary = f"Preview component for the {anim_name} animation with shared wrapper and interactive display."
        elif "index.ts" in fname and "/animations/" in path:
            parts = path.split("/")
            if len(parts) >= 3:
                anim_name = parts[2]
                tags.append("animation")
                tags.append("barrel")
                summary = f"Barrel re-export of the {anim_name} animation module from legacy definitions."
            else:
                summary = f"Module barrel file re-exporting public API."
        else:
            lib_part = path.split("/")[1]
            tags.append(lib_part)
            sub = fname.replace(".ts", "").replace(".tsx", "")
            if "index" in sub:
                summary = f"Module barrel exporting public API for the {lib_part} domain."
            elif "test" in sub or "__tests__" in path:
                tags.append("test")
                summary = f"Unit tests for the {lib_part} module."
            else:
                summary = f"Utility module providing {sub.replace('-', ' ')} functionality."
    # Tests
    elif path.startswith("tests/"):
        tags.append("test")
        test_part = path.split("/")[1]
        tags.append(test_part)
        test_name = fname.replace(".test.ts", "").replace(".test.tsx", "").replace(".spec.ts", "")
        summary = f"Test suite covering {test_name} component or utility."
    else:
        tags = ["code", "typescript"]
        summary = f"Project source file: {fname}."

    # Ensure minimum 3 tags
    base_tags = ["code", "typescript"]
    for t in base_tags:
        if t not in tags:
            tags.append(t)

    # If still less than 3, add generic tags
    fallback_tags = ["module", "source"]
    while len(tags) < 3 and fallback_tags:
        tag = fallback_tags.pop(0)
        if tag not in tags:
            tags.append(tag)

    node = {
        "id": f"file:{path}",
        "type": "file",
        "name": fname,
        "filePath": path,
        "summary": summary,
        "tags": tags[:5],
        "complexity": complexity,
    }
    return node

def should_skip_function(name, start_line, end_line, result):
    """Check if a function should be skipped per significance filter."""
    line_count = end_line - start_line
    is_exported = any(e.get("name") == name for e in result.get("exports", []))

    if line_count < 10 and not is_exported:
        return True

    # Skip trivial param generation functions
    if name == "generateStaticParams" and line_count <= 8:
        return True

    # Skip very short helpers
    if not is_exported and line_count < 12 and name in ["getTemplateSlugs", "SectionSkeleton"]:
        return True

    return False

def make_function_nodes(result):
    """Create function nodes with better analysis."""
    nodes = []
    path = result["path"]
    exported_names = {e["name"] for e in result.get("exports", [])}

    for func in result.get("functions", []):
        name = func["name"]
        start_line = func.get("startLine", 0)
        end_line = func.get("endLine", 0)
        params = func.get("params", [])

        if should_skip_function(name, start_line, end_line, result):
            continue

        line_count = end_line - start_line
        is_exported = name in exported_names

        complexity = "simple" if line_count < 30 else ("moderate" if line_count < 100 else "complex")

        tags = ["function"]

        # Categorize
        if name.endswith("Page") or name.endswith("Content"):
            tags.append("component")
            tags.append("react-component")
        elif name.startswith("generate"):
            tags.append("ssr")
            if "Metadata" in name:
                tags.append("seo")
        elif name.startswith("use"):
            tags.append("hook")
        elif "Handler" in name or "handle" in name.lower():
            tags.append("event-handler")
        else:
            tags.append("utility")

        if is_exported:
            tags.append("exported")

        # Build summary
        if name == "RootLayout":
            summary = "Root layout component rendering the HTML document shell with locale context, fonts, and global providers."
        elif name == "LocaleLayout":
            summary = "Locale layout component validating the locale parameter and wrapping children with i18n context."
        elif name == "Home":
            summary = "Home page component fetching style counts, animation counts, and template count for the landing display."
        elif name == "AnimationDetailContent":
            summary = "Animation detail content component rendering metadata, code snippets, CSS properties, and related animations."
        elif name == "AnimationDetailPage":
            summary = "Animation detail page with server-side data fetching, JSON-LD structured data, and content rendering."
        elif name == "BlogPostPage" or name == "BlogPage":
            summary = f"Blog page component fetching and rendering posts with structured data and navigation."
        elif name == "BlogListClient":
            summary = "Client-side blog listing with i18n support rendering post cards in a responsive grid."
        elif name == "ChangelogClient":
            summary = "Client-side changelog component rendering version entries and their changes."
        elif name == "GuidePage":
            summary = "Guide page rendering step-by-step CSS style guides with i18n support."
        elif name == "StyleGuidePage":
            summary = "Style guide detail page rendering guide content with influenced-by, use-cases, and references sections."
        elif name == "GuidesPage":
            summary = "Guides listing page displaying all style guides as cards with descriptions."
        elif name == "ComponentsPage":
            summary = "Interactive UI components showcase page with live prop controls and preview sections."
        elif name == "HtmlInCanvasPage":
            summary = "Interactive demo page rendering HTML content onto a Canvas element using experimental browser APIs."
        elif name == "PromptTopicContent":
            summary = "Prompt topic content component displaying prompts, related styles, FAQs, and use cases."
        elif name == "PromptTopicPage":
            summary = "Prompt topic page with server-side data fetching, related style lookup, and JSON-LD structured data."
        elif name == "PromptsPage":
            summary = "Prompts overview page categorizing and listing all prompt topics with descriptions."
        elif name == "PromptCard":
            summary = "Prompt card component with copy-to-clipboard and fallback textarea support."
        elif name == "FAQItem":
            summary = "Collapsible FAQ item component with toggle state management."
        elif name == "RecipeDetailContent":
            summary = "Recipe detail content component showing ingredients, related recipes, and copy-prompt functionality."
        elif name == "RecipeDetailPage":
            summary = "Recipe detail page with style resolution and related recipe calculation."
        elif name == "RecipesPage":
            summary = "Recipes listing page displaying all recipes with filtering and JSON-LD structured data."
        elif name == "StyleDetailPage":
            summary = "Style detail page with versioning, accessibility scoring, compatibility, and localized content."
        elif name == "StyleDetailLoading":
            summary = "Loading skeleton component for the style detail page."
        elif name == "StylesPage":
            summary = "Styles listing page with metadata and JSON-LD for SEO."
        elif name == "DarkModeUiPromptsPage":
            summary = "Dark mode UI prompts page rendering topic content with related styles and JSON-LD."
        elif name == "DashboardPromptsPage":
            summary = "Dashboard prompts page rendering topic content with related styles and JSON-LD."
        elif name == "LandingPagePromptsPage":
            summary = "Landing page prompts page rendering topic content with related styles and JSON-LD."
        elif name == "OGImage":
            summary = "OpenGraph image generation component for prompt topic pages."
        elif name == "sitemap":
            summary = "Sitemap generator producing localized URL entries for all content types."
        elif name == "robots":
            summary = "Robots.txt generator defining crawl rules and sitemap reference."
        elif name == "generateMetadata":
            summary = "Generates page-level metadata including title, description, and locale alternates for SEO."
        elif name == "generateStaticParams":
            summary = "Generates static route parameters for dynamic segment pre-rendering."
        elif name == "StyleGuidePage":
            summary = "Style guide detail page rendering full guide content with navigation."
        elif name == "StyleGuidePage":
            summary = "Style guide detail page with influencedBy, useCases, and references sections."
        else:
            summary = f"Function implementing the {name} logic within the module."

        if len(tags) < 3:
            extras = [t for t in ["code", "typescript"] if t not in tags]
            tags.extend(extras)

        node = {
            "id": f"function:{path}:{name}",
            "type": "function",
            "name": name,
            "filePath": path,
            "lineRange": [start_line, end_line],
            "summary": summary,
            "tags": tags[:5],
            "complexity": complexity,
        }
        nodes.append(node)

    return nodes


def make_legacy_function_nodes(path, result):
    """For legacy anim files that export objects, read source to find function-like definitions."""
    nodes = []
    fname = get_file_name(path)
    exported = [e["name"] for e in result.get("exports", [])]

    # Legacy files have a top-level variable assignment like:
    # export const pulseRing: Animation = { ... }
    # We'll create function nodes for the exported variables that are significant
    for export_name in exported:
        # These are animation definitions, not functions, but we should treat them
        # as conceptually significant
        pass  # We'll handle via file-level nodes only; animation defs are data

    return nodes


def process_batch(batch_index, input_data, struct_data):
    nodes = []
    edges = []
    batch_files = input_data["batchFiles"]
    batch_imports = input_data.get("batchImportData", {})

    struct_by_path = {}
    for r in struct_data.get("results", []):
        struct_by_path[r["path"]] = r

    # Create file nodes, function nodes, class nodes
    for bf in batch_files:
        path = bf["path"]
        result = struct_by_path.get(path)

        if not result:
            fname = get_file_name(path)
            nodes.append({
                "id": f"file:{path}",
                "type": "file",
                "name": fname,
                "filePath": path,
                "summary": f"{fname} - project file.",
                "tags": ["code", "typescript"],
                "complexity": "simple",
            })
            continue

        file_node = make_file_node(result, bf)
        nodes.append(file_node)

        func_nodes = make_function_nodes(result)
        nodes.extend(func_nodes)

        class_nodes = []
        for cls in result.get("classes", []):
            name = cls["name"]
            methods = cls.get("methods", [])
            if len(methods) < 2:
                s = cls.get("startLine", 0); e = cls.get("endLine", 0)
                if (e - s) < 20:
                    continue

            tags = ["class", "typescript"]
            if "Boundary" in name or "Error" in name:
                tags.append("error-boundary")
            elif "Provider" in name or "Context" in name:
                tags.append("context")
            elif "Service" in name:
                tags.append("service")
            elif "Handler" in name:
                tags.append("handler")
            elif "Controller" in name:
                tags.append("controller")
            elif "Model" in name:
                tags.append("data-model")
            if len(tags) < 3:
                tags.append("component")

            node = {
                "id": f"class:{path}:{name}",
                "type": "class",
                "name": name,
                "filePath": path,
                "lineRange": [cls.get("startLine", 0), cls.get("endLine", 0)],
                "summary": f"Class providing {name} functionality with {len(methods)} methods.",
                "tags": tags[:5],
                "complexity": "moderate" if len(methods) > 3 else "simple",
            }
            nodes.append(node)
            class_nodes.append(node)

        # Contains + exports edges
        for fn in func_nodes:
            edges.append({"source": f"file:{path}", "target": fn["id"], "type": "contains", "direction": "forward", "weight": 1.0})
            if fn["name"] in {e["name"] for e in result.get("exports", [])}:
                edges.append({"source": f"file:{path}", "target": fn["id"], "type": "exports", "direction": "forward", "weight": 0.8})

        for cn in class_nodes:
            edges.append({"source": f"file:{path}", "target": cn["id"], "type": "contains", "direction": "forward", "weight": 1.0})

    # Import edges (always all of them)
    for bf in batch_files:
        path = bf["path"]
        imports = batch_imports.get(path, [])
        for imp in imports:
            edges.append({"source": f"file:{path}", "target": f"file:{imp}", "type": "imports", "direction": "forward", "weight": 0.7})

    return nodes, edges


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    for batch_index in range(15, 22):
        input_path = os.path.join(TMP_DIR, f"ua-file-analyzer-input-{batch_index}.json")
        struct_path = os.path.join(TMP_DIR, f"ua-file-analyzer-struct-{batch_index}.json")
        output_path = os.path.join(OUT_DIR, f"batch-{batch_index}.json")

        if not os.path.exists(input_path):
            print(f"SKIP: input for batch {batch_index} not found")
            continue
        if not os.path.exists(struct_path):
            print(f"SKIP: struct for batch {batch_index} not found")
            continue

        input_data = load_json(input_path)
        struct_data = load_json(struct_path)

        nodes, edges = process_batch(batch_index, input_data, struct_data)

        # Verify import counts
        expected_imports = sum(len(v) for v in input_data.get("batchImportData", {}).values())
        actual_imports = sum(1 for e in edges if e["type"] == "imports")
        assert actual_imports == expected_imports, f"Batch {batch_index}: expected {expected_imports} imports, got {actual_imports}"

        result = {"nodes": nodes, "edges": edges}

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"Batch {batch_index}: {len(nodes)} nodes, {len(edges)} edges (imports: {actual_imports}/{expected_imports})")


if __name__ == "__main__":
    main()
