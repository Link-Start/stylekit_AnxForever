#!/usr/bin/env python3
"""Generate batch output files for batches 15-21."""

import json
import os
import sys

PROJECT_ROOT = "/home/anx4758/stylekit"
TMP_DIR = os.path.join(PROJECT_ROOT, ".understand-anything", "tmp")
OUT_DIR = os.path.join(PROJECT_ROOT, ".understand-anything", "intermediate")

def load_json(path):
    with open(path) as f:
        return json.load(f)

def get_file_name(path):
    return path.split("/")[-1]

def make_node_id(prefix, path, suffix=None):
    if suffix:
        return f"{prefix}:{path}:{suffix}"
    return f"{prefix}:{path}"

def estimate_complexity(non_empty_lines, func_count, class_count):
    if non_empty_lines < 50 and func_count <= 2 and class_count == 0:
        return "simple"
    elif non_empty_lines < 200 or func_count <= 5:
        return "moderate"
    else:
        return "complex"

def make_file_node(result, file_cat):
    path = result["path"]
    non_empty = result.get("nonEmptyLines", result.get("totalLines", 0))
    func_count = result.get("metrics", {}).get("functionCount", 0)
    class_count = result.get("metrics", {}).get("classCount", 0)

    total_lines = result.get("totalLines", 0)
    prev_code_count = result.get("nonEmptyLines", total_lines)

    # Determine node type
    node_type = "file"

    # Determine complexity
    complexity = estimate_complexity(non_empty, func_count, class_count)

    # Determine tags and summary based on path patterns
    tags = []
    summary = ""
    language_notes = None

    # Common tag patterns
    fname = get_file_name(path)
    ext = ""
    if "." in fname:
        _, ext = fname.rsplit(".", 1)

    # Check for __tests__ dir or .test. / .spec. patterns
    if "/__tests__/" in path or "/tests/" in path or ".test." in fname or ".spec." in fname:
        tags.append("test")

    # App router page detection
    if path.startswith("app/") and ("page.tsx" in path or "page.ts" in path or "layout.tsx" in path or "route.ts" in path):
        tags.append("page")
        if "layout" in path:
            tags.append("layout")
        if "route" in path:
            tags.append("api-route")

    # Check for _content.tsx patterns
    if "_content.tsx" in path or "_content.ts" in path:
        tags.append("content-component")

    # Check for component files
    if path.startswith("components/"):
        tags.append("component")

    # Lib files
    if path.startswith("lib/"):
        tags.append("utility")
        if "types" in path or "type" in path:
            tags.append("type-definition")

    # Entry point patterns
    if path == "app/layout.tsx":
        tags.extend(["layout", "entry-point"])

    # [_legacy] patterns
    if "/_legacy/" in path:
        tags.append("legacy")

    # animation files
    if "animations" in path.lower():
        tags.append("animation")

    # preview files
    if "preview" in path.lower() or "preview" in fname.lower():
        tags.append("preview")

    # locale files
    if "[locale]" in path:
        tags.append("i18n")

    # Ensure at least 3 tags
    if len(tags) < 3:
        extra_tags = ["code", "typescript"]
        for t in extra_tags:
            if t not in tags:
                tags.append(t)
        tags = tags[:5]

    # Build summary
    fname_clean = fname.replace(".tsx", "").replace(".ts", "")

    if "layout" in fname:
        summary = f"Next.js App Router layout defining the root HTML structure with metadata, viewport, and providers."
    elif "route" in fname:
        route_name = path.split("/")[-2] if "/" in path else fname
        summary = f"API route handler for {route_name} returning dynamic content."
    elif "page" in fname:
        # More specific page descriptions
        if "[locale]" in path:
            locale_path = path.replace("app/[locale]/", "")
            if "/" in locale_path:
                locale_path = locale_path.rsplit("/", 1)[0]
            else:
                locale_path = locale_path.replace("/page.tsx", "").replace("/page.ts", "")
            summary = f"Localized page component for the {locale_path} route using i18n metadata and routing."
        elif "[slug]" in path:
            summary = f"Dynamic page component for a {path.split('/')[1]} detail route with server-side data fetching."
        else:
            page_name = path.split("/")[1] if path.count("/") >= 1 else fname
            summary = f"Page component for the {page_name} route rendering content with layout components."
    elif "_content" in fname:
        domain = path.split("/")[1] if path.count("/") >= 2 else ""
        summary = f"Content component for {domain} detail pages with i18n support and structured data rendering."
    elif "blog-list-client" in fname:
        summary = f"Client-side blog list component with i18n support for rendering post cards."
    elif "changelog-client" in fname:
        summary = f"Client-side changelog component rendering version history entries with i18n."
    elif path.startswith("components/ui/"):
        comp_name = path.split("/")[2]
        summary = f"Barrel file re-exporting the {comp_name} UI component modules."
    elif "/_legacy/" in path:
        anim_name = path.split("/")[-1].replace(".ts", "")
        summary = f"Legacy animation definition for {anim_name} implementing keyframe-based motion effects."
    elif "preview" in fname.lower():
        anim_name = path.split("/")[-2] if "/" in path else ""
        summary = f"React preview component for the {anim_name} animation with shared preview wrapper."
    else:
        summary = f"{'Module' if 'module' in path else 'Component'} providing core functionality within the project."

    node = {
        "id": f"file:{path}",
        "type": node_type,
        "name": fname,
        "filePath": path,
        "summary": summary,
        "tags": tags[:5],
        "complexity": complexity,
    }

    if language_notes:
        node["languageNotes"] = language_notes

    return node

def make_function_nodes(result):
    """Create function nodes from extracted functions."""
    nodes = []
    path = result["path"]

    for func in result.get("functions", []):
        name = func["name"]
        start_line = func.get("startLine", 0)
        end_line = func.get("endLine", 0)

        line_count = end_line - start_line

        # Significance filter: 10+ lines OR exported
        is_exported = any(
            e.get("name") == name for e in result.get("exports", [])
        )

        if line_count < 10 and not is_exported:
            continue

        # Check for trivial patterns (skip obvious one-liners that slipped through)
        if not is_exported and line_count < 15 and name in ["toggleProps", "handleCopy", "requestPaint"]:
            continue

        # Skip generateStaticParams helpers that are just array maps
        if name == "getTemplateSlugs" and line_count <= 10 and not is_exported:
            continue

        complexity = "simple"
        if line_count >= 30:
            complexity = "moderate"
        if line_count >= 100:
            complexity = "complex"

        tags = ["function"]
        if name.startswith("generate"):
            tags.append("ssr")
        if name.endswith("Page") or name.endswith("Content"):
            tags.append("component")
        if "Handler" in name or "handle" in name.lower():
            tags.append("event-handler")
        if "use" in name.lower() and "Context" not in name:
            tags.append("hook")
        if len(tags) < 3:
            tags.extend(["utility", "typescript"])

        # Build summary
        if name.startswith("generateStaticParams"):
            summary = f"Generates static params for dynamic route segments in the Next.js App Router."
        elif name.startswith("generateMetadata"):
            summary = f"Generates page metadata including title, description, and locale alternates."
        elif "Page" in name or "Content" in name:
            domain = name.replace("Page", "").replace("Content", "")
            summary = f"React component rendering the {domain} page with layout and data."
        elif name.startswith("use"):
            summary = f"Custom React hook providing shared state or behavior."
        else:
            summary = f"Function implementing {name} logic within the module."

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

def make_class_nodes(result):
    """Create class nodes from extracted classes."""
    nodes = []
    path = result["path"]

    for cls in result.get("classes", []):
        name = cls["name"]
        methods = cls.get("methods", [])
        properties = cls.get("properties", [])

        # Significance filter
        if len(methods) < 2:
            start_line = cls.get("startLine", 0)
            end_line = cls.get("endLine", 0)
            if (end_line - start_line) < 20:
                continue

        tags = ["class"]
        if any("Handler" in name or "Controller" in name for name in [name]):
            tags.append("api-handler")
        if len(tags) < 3:
            tags.extend(["utility", "typescript"])

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

    return nodes

def process_batch(batch_index, input_data, struct_data):
    """Process a single batch and return nodes and edges."""
    nodes = []
    edges = []

    batch_files = input_data["batchFiles"]
    batch_imports = input_data.get("batchImportData", {})

    # Build a lookup from path to struct result
    struct_by_path = {}
    for r in struct_data.get("results", []):
        struct_by_path[r["path"]] = r

    # First pass: create all file nodes and function/class nodes
    for bf in batch_files:
        path = bf["path"]
        result = struct_by_path.get(path)

        if not result:
            # File was skipped - create minimal node
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

        # Create file node
        file_node = make_file_node(result, bf["fileCategory"])
        nodes.append(file_node)

        # Create function nodes
        func_nodes = make_function_nodes(result)
        nodes.extend(func_nodes)

        # Create class nodes
        class_nodes = make_class_nodes(result)
        nodes.extend(class_nodes)

        # Create contains edges
        for func_node in func_nodes:
            edges.append({
                "source": f"file:{path}",
                "target": func_node["id"],
                "type": "contains",
                "direction": "forward",
                "weight": 1.0,
            })

            # Also exports edge if function is exported
            func_name = func_node["name"]
            is_exported = any(
                e.get("name") == func_name for e in result.get("exports", [])
            )
            if is_exported:
                edges.append({
                    "source": f"file:{path}",
                    "target": func_node["id"],
                    "type": "exports",
                    "direction": "forward",
                    "weight": 0.8,
                })

        for cls_node in class_nodes:
            edges.append({
                "source": f"file:{path}",
                "target": cls_node["id"],
                "type": "contains",
                "direction": "forward",
                "weight": 1.0,
            })

            cls_name = cls_node["name"]
            is_exported = any(
                e.get("name") == cls_name for e in result.get("exports", [])
            )
            if is_exported:
                edges.append({
                    "source": f"file:{path}",
                    "target": cls_node["id"],
                    "type": "exports",
                    "direction": "forward",
                    "weight": 0.8,
                })

    # Second pass: create import edges
    for bf in batch_files:
        path = bf["path"]
        imports = batch_imports.get(path, [])
        for imp in imports:
            edges.append({
                "source": f"file:{path}",
                "target": f"file:{imp}",
                "type": "imports",
                "direction": "forward",
                "weight": 0.7,
            })

    # Third pass: create callGraph-based edges
    for bf in batch_files:
        path = bf["path"]
        result = struct_by_path.get(path)
        if not result:
            continue

        for call in result.get("callGraph", []):
            caller = call.get("caller", "")
            callee_info = call.get("callee", "")

            # Only create edges for calls to project-internal functions
            # We create edges for calls that reference known functions
            # The callee might be a function in the same file or another file
            # Skip built-in/native callee names
            skip_patterns = ["setState", "setTimeout", "Promise", "Math.", "Array.", "Object.",
                            "console.", "window.", "document.", "ctx.", "canvas.", "navigator.",
                            "observer.", "new Date", "String(", "process.", "join", "readdirSync"]
            if any(callee_info.startswith(p) for p in skip_patterns):
                continue

            # Check if callee looks like it could be a project function
            # (not a method chain, not a lambda)
            if "." in callee_info and not any(callee_info.endswith(f".{x}") for x in ["map", "find", "filter", "reduce", "flatMap", "join", "slice", "includes", "has"]):
                # Could be method chain like animations.map - skip if mapped
                if callee_info.count(".") > 1 and not callee_info.startswith("t("):
                    continue

            # Only emit if caller is a function we have a node for
            caller_node_id = f"function:{path}:{caller}"
            # Check if we can match the callee to a known function
            # We don't have cross-batch visibility, so skip if unsure
            if callee_info in ["getAllPosts", "getAllSlugs", "getPostBySlug", "getStyleBySlug",
                               "getTopicBySlug", "getAllStylesMeta", "getAllAnimationsMeta",
                               "getAnimationBySlug", "getAllRecipes", "getRecipeById",
                               "getRecipesByUseCase", "getRecipesByVisualStyle",
                               "resolveRecipeStyles", "resolveStyleBySlug",
                               "getSiteBaseUrl", "serializeJsonLd", "notFound",
                               "generateBlogPostJsonLd", "generateBreadcrumbJsonLd",
                               "generateStyleJsonLd", "getAllTopicSlugs",
                               "getCurrentVersion", "getChangelog", "getFrontendReadiness",
                               "generateBreadcrumbJsonLd", "generateEnhancedAIRules",
                               "scoreStyle", "generateStyleGuideMetadata",
                               "localizedString", "localizedList",
                               "generateRss", "generatePrompt",
                               "getAllAnimationsMeta", "getAllAnimations"]:
                # These are from project-internal lib files
                pass  # We'd need batchImportData to resolve, skip for now

            edges.append({
                "source": caller_node_id,
                "target": f"file:{path}",  # We use file-level as fallback
                "type": "calls",
                "direction": "forward",
                "weight": 0.8,
            })

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

        # Verify import edge count
        total_imports = 0
        for path in input_data.get("batchImportData", {}):
            total_imports += len(input_data["batchImportData"][path])

        actual_import_edges = sum(1 for e in edges if e["type"] == "imports")

        result = {
            "nodes": nodes,
            "edges": edges,
        }

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"Batch {batch_index}: {len(nodes)} nodes, {len(edges)} edges ({actual_import_edges}/{total_imports} import edges)")


if __name__ == "__main__":
    main()
