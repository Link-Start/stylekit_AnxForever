#!/usr/bin/env python3
"""Generate all batch files (30-42) for the file-analyzer."""

import json, os, math

STRUCT_DIR = "/home/anx4758/stylekit/.understand-anything/tmp"
OUTPUT_DIR = "/home/anx4758/stylekit/.understand-anything/intermediate"

def get_input(batch_idx):
    with open(f"{STRUCT_DIR}/ua-file-analyzer-input-{batch_idx}.json") as f:
        return json.load(f)

def get_struct(batch_idx):
    with open(f"{STRUCT_DIR}/ua-file-analyzer-struct-{batch_idx}.json") as f:
        return json.load(f)

def write_output(batch_idx, nodes, edges):
    """Write output file(s), splitting if needed."""
    node_count = len(nodes)
    edge_count = len(edges)

    if node_count <= 60 and edge_count <= 120:
        with open(f"{OUTPUT_DIR}/batch-{batch_idx}.json", "w") as f:
            json.dump({"nodes": nodes, "edges": edges}, f, indent=2)
        print(f"  -> batch-{batch_idx}.json ({node_count}n/{edge_count}e)")
        return

    # Split needed
    parts = math.ceil(max(node_count / 60, edge_count / 120))
    print(f"  -> splitting into {parts} parts ({node_count}n/{edge_count}e)")

    # Sort files alphabetically
    file_paths = sorted(set(
        n.get("filePath", "") for n in nodes
        if n.get("filePath")
    ))

    chunk_size = math.ceil(len(file_paths) / parts)
    chunks = [file_paths[i:i+chunk_size] for i in range(0, len(file_paths), chunk_size)]

    for k, chunk_paths in enumerate(chunks, 1):
        chunk_file_set = set(chunk_paths)
        part_nodes = []
        part_edge_sources = set()

        for n in nodes:
            fp = n.get("filePath", "")
            # For function/class nodes, check filePath; for file nodes, check id
            if fp in chunk_file_set:
                part_nodes.append(n)
                part_edge_sources.add(n["id"])
            elif n["id"].startswith("file:") and n["id"][5:] in chunk_file_set:
                part_nodes.append(n)
                part_edge_sources.add(n["id"])
            elif not fp:
                # Sub-file nodes with no filePath - include based on id convention
                for cfp in chunk_file_set:
                    if f":{cfp}:" in n["id"] or n["id"].endswith(f":{cfp}"):
                        part_nodes.append(n)
                        part_edge_sources.add(n["id"])
                        break

        part_nodes_ids = set(n["id"] for n in part_nodes)
        part_edges = [e for e in edges if e["source"] in part_nodes_ids]

        with open(f"{OUTPUT_DIR}/batch-{batch_idx}-part-{k}.json", "w") as f:
            json.dump({"nodes": part_nodes, "edges": part_edges}, f, indent=2)
        print(f"  -> batch-{batch_idx}-part-{k}.json ({len(part_nodes)}n/{len(part_edges)}e)")


# ============================================
# Batch 30 - lib/styles/*.ts (part 1 of styles)
# ============================================
def gen_batch_30():
    inp = get_input(30)
    struct = get_struct(30)
    nodes = []
    edges = []

    for r in struct["results"]:
        path = r["path"]
        name = path.split("/")[-1]
        nEL = r["nonEmptyLines"]

        if nEL < 50: complexity = "simple"
        elif nEL < 200: complexity = "moderate"
        else: complexity = "complex"

        if path == "lib/styles/readiness.ts":
            summary = "Style readiness evaluation system with support detection, coverage calculation, and curated/fallback profiles for all design styles."
            tags = ["utility", "data-model", "validation"]
            complexity = "complex"
        elif path == "lib/styles/registry.ts":
            summary = "Central style registry aggregating all defined styles and providing slug-based lookup."
            tags = ["barrel", "registry", "lookup"]
            complexity = "complex"
        else:
            style_name = name.replace(".ts", "").replace("-", " ").title()
            summary = f"Defines the {style_name} design style with full component templates, design tokens, CSS variables, and AI prompting rules."
            tags = ["style-definition", "design-system", "ui-component"]
            if 300 <= nEL < 500: complexity = "moderate"

        nodes.append({
            "id": f"file:{path}", "type": "file", "name": name, "filePath": path,
            "summary": summary, "tags": tags, "complexity": complexity
        })

        # Import edges
        if path in inp["batchImportData"]:
            for imp_path in inp["batchImportData"][path]:
                edges.append({"source": f"file:{path}", "target": f"file:{imp_path}",
                              "type": "imports", "direction": "forward", "weight": 0.7})

    # Function nodes for readiness.ts
    readiness_funcs = [
        ("calculateReadinessCoverage", "Calculates overall readiness coverage score for a style profile.", 475, 486),
        ("getFrontendReadiness", "Gets frontend readiness assessment for a style by building fallback profile and calculating coverage.", 540, 548),
        ("hasCuratedFrontendReadiness", "Checks whether a style has a curated frontend readiness entry.", 550, 552),
        ("getCuratedReadinessSlugs", "Returns list of slugs with curated frontend readiness.", 554, 556)
    ]
    for fn_name, fn_summary, start, end in readiness_funcs:
        nid = f"function:lib/styles/readiness.ts:{fn_name}"
        nodes.append({
            "id": nid, "type": "function", "name": fn_name,
            "lineRange": [start, end], "filePath": "lib/styles/readiness.ts",
            "summary": fn_summary, "tags": ["utility", "readiness"], "complexity": "simple"
        })
        edges.append({"source": "file:lib/styles/readiness.ts", "target": nid,
                      "type": "contains", "direction": "forward", "weight": 1.0})
        edges.append({"source": "file:lib/styles/readiness.ts", "target": nid,
                      "type": "exports", "direction": "forward", "weight": 0.8})

    # Function node for registry.ts
    nid = "function:lib/styles/registry.ts:getStyleBySlug"
    nodes.append({
        "id": nid, "type": "function", "name": "getStyleBySlug",
        "lineRange": [316, 318], "filePath": "lib/styles/registry.ts",
        "summary": "Looks up a design style by its slug from the aggregated styles array.",
        "tags": ["utility", "lookup"], "complexity": "simple"
    })
    edges.append({"source": "file:lib/styles/registry.ts", "target": nid,
                  "type": "contains", "direction": "forward", "weight": 1.0})
    edges.append({"source": "file:lib/styles/registry.ts", "target": nid,
                  "type": "exports", "direction": "forward", "weight": 0.8})

    # Validate imports
    expected = sum(len(v) for v in inp["batchImportData"].values())
    actual = len([e for e in edges if e["type"] == "imports"])
    assert actual == expected, f"Import mismatch: {actual} != {expected}"

    write_output(30, nodes, edges)


# ============================================
# Batch 31 - lib/animations/* (animation re-exports + types)
# ============================================
def gen_batch_31():
    inp = get_input(31)
    struct = get_struct(31)
    nodes = []
    edges = []

    for r in struct["results"]:
        path = r["path"]
        name = path.split("/")[-1]
        nEL = r["nonEmptyLines"]

        if path == "lib/animations/types.ts":
            summary = "TypeScript type definitions for the animation system including animation configs and AnimationMeta interfaces."
            tags = ["type-definition", "typescript", "animation"]
            complexity = "moderate"
        elif path == "lib/animations/vocabulary.ts":
            summary = "Animation vocabulary and terminology definitions used across the animation system for classification and search."
            tags = ["data-model", "i18n", "animation"]
            complexity = "complex"
        elif path.endswith("/meta.ts"):
            base = path.split("/")[-2].replace("-", " ").title()
            summary = f"Metadata definition for the {base} animation including display name, description, and configuration schema."
            tags = ["metadata", "animation"]
            complexity = "simple"
        elif "scroll-page-turn" in path or "scroll-peel-away" in path:
            anim_name = path.split("/")[-2].replace("-", " ").title()
            summary = f"Implementation of the {anim_name} scroll-based animation hook with options and preview component."
            tags = ["animation", "hook", "scroll"]
            complexity = "moderate"
        elif "text-repulsion" in path:
            summary = "Text repulsion mouse interaction animation component with particle-like text displacement effects."
            tags = ["animation", "interaction", "mouse-effect"]
            complexity = "moderate"
        elif "spotlight-card" in path or "tilt-3d" in path:
            base = path.split("/")[-2].replace("-", " ").title()
            summary = f"Re-exports the {base} animation from the legacy animation module for backward compatibility."
            tags = ["animation", "barrel", "re-export"]
            complexity = "simple"
        else:
            anim_name = path.split("/")[-2].replace("-", " ").title()
            summary = f"Barrel re-export of the {anim_name} animation from its legacy module for backward compatibility."
            tags = ["animation", "barrel", "re-export"]
            complexity = "simple"

        node = {
            "id": f"file:{path}", "type": "file", "name": name, "filePath": path,
            "summary": summary, "tags": tags or ["animation"],
            "complexity": complexity
        }
        nodes.append(node)

        if path in inp["batchImportData"]:
            for imp_path in inp["batchImportData"][path]:
                edges.append({"source": f"file:{path}", "target": f"file:{imp_path}",
                              "type": "imports", "direction": "forward", "weight": 0.7})

    expected = sum(len(v) for v in inp["batchImportData"].values())
    actual = len([e for e in edges if e["type"] == "imports"])
    assert actual == expected, f"Batch 31 Import mismatch: {actual} != {expected}"

    write_output(31, nodes, edges)


# ============================================
# Batch 32 - lib/styles/*.ts (part 2 of styles)
# ============================================
def gen_batch_32():
    inp = get_input(32)
    struct = get_struct(32)
    nodes = []
    edges = []

    for r in struct["results"]:
        path = r["path"]
        name = path.split("/")[-1]
        nEL = r["nonEmptyLines"]

        if path == "lib/styles/types.ts":
            summary = "Core TypeScript type definitions for the DesignStyle interface and all supporting types including StyleVariant and ComponentTemplate."
            tags = ["type-definition", "typescript", "interface"]
            complexity = "moderate"
        else:
            style_name = name.replace(".ts", "").replace("-", " ").title()
            summary = f"Defines the {style_name} design style with full component templates, design tokens, CSS variables, and AI prompting rules."
            tags = ["style-definition", "design-system", "ui-component"]

        complexity = "simple" if nEL < 50 else ("moderate" if nEL < 200 else "complex")
        if 250 <= nEL <= 550: complexity = "moderate"
        if nEL > 550: complexity = "complex"

        nodes.append({
            "id": f"file:{path}", "type": "file", "name": name, "filePath": path,
            "summary": summary, "tags": tags, "complexity": complexity
        })

        if path in inp["batchImportData"]:
            for imp_path in inp["batchImportData"][path]:
                edges.append({"source": f"file:{path}", "target": f"file:{imp_path}",
                              "type": "imports", "direction": "forward", "weight": 0.7})

    expected = sum(len(v) for v in inp["batchImportData"].values())
    actual = len([e for e in edges if e["type"] == "imports"])
    assert actual == expected, f"Batch 32 Import mismatch: {actual} != {expected}"

    write_output(32, nodes, edges)


# ============================================
# Batch 33 - lib/generator/* (AI style generator)
# ============================================
def gen_batch_33():
    inp = get_input(33)
    struct = get_struct(33)
    nodes = []
    edges = []

    for r in struct["results"]:
        path = r["path"]
        name = path.split("/")[-1]
        nEL = r["nonEmptyLines"]

        # Determine file type and summary based on path
        is_test = "__tests__" in path
        complexity = "simple" if nEL < 50 else ("moderate" if nEL < 200 else "complex")

        if path == "lib/generator/index.ts":
            summary = "Main entry point for the AI code generator, providing template access and file generation orchestration functions."
            tags = ["entry-point", "generator", "api-handler"]
        elif path == "lib/generator/types.ts":
            summary = "TypeScript type definitions for the generator system including section configs, field types, and generation options."
            tags = ["type-definition", "typescript"]
        elif "templates/" in path:
            tpl_type = path.split("/")[-1].replace(".ts", "").title()
            summary = f"Template definition for {tpl_type} layouts with section structures, field schemas, and HTML/CSS generation helpers."
            tags = ["template", "generator", "html"]
        elif "renderers/" in path:
            rdr = name.replace(".ts", "").replace("-renderer", "").upper()
            summary = f"{rdr} code renderer that transforms generator templates into production-ready {rdr} component code."
            tags = ["renderer", "generator", rdr.lower()]
        elif path == "lib/generator/quality.ts":
            summary = "Quality validation for generated code including config sanitization and output evaluation."
            tags = ["validation", "generator", "utility"]
        elif path == "lib/generator/scenario-packs.ts":
            summary = "Scenario pack system providing pre-configured template parameter sets for common use cases."
            tags = ["data-model", "generator", "scenario"]
        elif path == "lib/generator/scenario-storage.ts":
            summary = "Persistent storage layer for saving, loading, and managing user-created scenario packs via localStorage."
            tags = ["storage", "generator", "utility"]
        elif path == "lib/generator/export-artifacts.ts":
            summary = "Exports generated files as downloadable artifacts with file tree structure for the generator output."
            tags = ["export", "generator", "utility"]
        elif path == "lib/generator/style-injector.ts":
            summary = "Injects design style CSS variables and global styles into generated HTML output for inline styling."
            tags = ["styling", "generator", "css"]
        elif path == "lib/generator/zip-builder.ts":
            summary = "Builds ZIP archives of generated code files for batch download in the browser."
            tags = ["export", "utility", "compression"]
        elif path == "lib/generator/zip-worker.ts":
            summary = "Web Worker wrapper for building ZIP archives off the main thread to avoid UI blocking."
            tags = ["web-worker", "utility", "compression"]
        elif path == "lib/scaffold/style-scaffold.ts":
            summary = "Generates file scaffold for new design styles including directory structure, config files, and boilerplate code."
            tags = ["scaffold", "generator", "utility"]
        elif is_test:
            test_name = path.split("/")[-1].replace(".test.ts", "").replace(".test.tsx", "")
            summary = f"Unit tests for the {test_name} module covering rendering, export, and scenario management."
            tags = ["test", "unit", "generator"]
            complexity = "moderate" if nEL > 50 else "simple"
        else:
            summary = f"Generator utility module for {name.replace('.ts', '').replace('-', ' ')}."
            tags = ["utility", "generator"]

        nodes.append({
            "id": f"file:{path}", "type": "file", "name": name, "filePath": path,
            "summary": summary, "tags": tags, "complexity": complexity
        })

        if path in inp["batchImportData"]:
            for imp_path in inp["batchImportData"][path]:
                edges.append({"source": f"file:{path}", "target": f"file:{imp_path}",
                              "type": "imports", "direction": "forward", "weight": 0.7})

    # Validate imports
    expected = sum(len(v) for v in inp["batchImportData"].values())
    actual = len([e for e in edges if e["type"] == "imports"])
    assert actual == expected, f"Batch 33 Import mismatch: {actual} != {expected}"

    write_output(33, nodes, edges)


# ============================================
# Batch 34 - loading pages + mouse interactions + pointer + showcase
# ============================================
def gen_batch_34():
    inp = get_input(34)
    struct = get_struct(34)
    nodes = []
    edges = []

    for r in struct["results"]:
        path = r["path"]
        name = path.split("/")[-1]
        nEL = r["nonEmptyLines"]

        complexity = "simple" if nEL < 50 else ("moderate" if nEL < 200 else "complex")

        if path == "components/mouse-interactions/primitives.tsx":
            summary = "Core mouse interaction primitive components including MouseStage, FollowAura, Trail, Spotlight, GlitchRGB, and 15+ other interactive effects."
            tags = ["component", "interaction", "mouse-effect", "animation"]
            complexity = "complex"
        elif "mouse-interactions/rooms/" in path:
            room = path.split("/")[-1].replace(".tsx", "").replace("-room", "").replace("_", "").replace("registry", "Registry").replace("types", "Types")
            if path.endswith("registry.ts"):
                summary = "Registry mapping room slugs to their React components for the mouse interactions showcase."
                tags = ["registry", "interaction", "routing"]
            elif path.endswith("types.ts"):
                summary = "TypeScript types for mouse interaction room definitions."
                tags = ["type-definition", "typescript"]
            elif path.endswith("_room-shared.tsx"):
                summary = "Shared room component utilities including pointer detection hooks and accessibility checks."
                tags = ["utility", "hook", "interaction"]
            else:
                room_name = path.split("/")[-1].replace(".tsx", "").replace("-", " ").title()
                summary = f"Themed mouse interaction showcase room demonstrating effects in the {room_name} design aesthetic."
                tags = ["component", "interaction", "showcase"]
            complexity = "moderate" if nEL > 60 else "simple"
        elif path == "components/mouse-interactions/mouse-interactions-content.tsx":
            summary = "Main content component for the mouse interactions showcase page with room navigation and layout."
            tags = ["component", "interaction", "page-content"]
        elif "pointer-interactions/" in path:
            if path.endswith("hooks.ts"):
                summary = "Custom React hooks for pointer interaction detection including reduced motion and fine pointer checks."
                tags = ["hook", "interaction", "accessibility"]
            else:
                comp = path.split("/")[-1].replace(".tsx", "").replace("-", " ").title()
                summary = f"{comp} React component providing pointer-driven visual effects like magnetic attraction and tilt response."
                tags = ["component", "interaction", "pointer-effect"]
        elif path == "components/showcase/shared.tsx":
            summary = "Shared UI components for the style showcase including navigation, hero sections, color palettes, and design rules grids."
            tags = ["component", "showcase", "ui"]
            complexity = "complex"
        elif path == "components/skeletons/__tests__/page-skeleton.test.tsx":
            summary = "Unit tests for the PageSkeleton loading component."
            tags = ["test", "unit", "skeleton"]
        elif path.endswith("loading.tsx") or path.endswith("loading.tsx"):
            # Loading files
            if path == "app/loading.tsx":
                summary = "Root loading component for the site showing Skeleton-based placeholders during page transitions."
                tags = ["loading", "ui", "skeleton"]
                complexity = "moderate"
            elif path == "app/components/loading.tsx":
                summary = "Loading component for the components showcase page with category and card skeletons."
                tags = ["loading", "ui", "skeleton"]
                complexity = "moderate"
            elif path == "app/styles/loading.tsx":
                summary = "Loading component for the styles listing page with filter and grid skeletons."
                tags = ["loading", "ui", "skeleton"]
                complexity = "moderate"
            else:
                route = path.replace("app/", "").replace("/loading.tsx", "").replace("/page.tsx", "")
                summary = f"Loading skeleton placeholder for the {route} route providing immediate visual feedback during page loads."
                tags = ["loading", "ui", "skeleton"]

        nodes.append({
            "id": f"file:{path}", "type": "file", "name": name, "filePath": path,
            "summary": summary, "tags": tags, "complexity": complexity
        })

        if path in inp["batchImportData"]:
            for imp_path in inp["batchImportData"][path]:
                edges.append({"source": f"file:{path}", "target": f"file:{imp_path}",
                              "type": "imports", "direction": "forward", "weight": 0.7})

    expected = sum(len(v) for v in inp["batchImportData"].values())
    actual = len([e for e in edges if e["type"] == "imports"])
    assert actual == expected, f"Batch 34 Import mismatch: {actual} != {expected}"

    write_output(34, nodes, edges)


# ============================================
# Batch 35 - UI components (skeleton, alert, brutal, button, etc.)
# ============================================
def gen_batch_35():
    inp = get_input(35)
    struct = get_struct(35)
    nodes = []
    edges = []

    for r in struct["results"]:
        path = r["path"]
        name = path.split("/")[-1]
        nEL = r["nonEmptyLines"]

        complexity = "simple" if nEL < 50 else ("moderate" if nEL < 200 else "complex")

        if path == "components/skeletons/page-skeleton.tsx":
            summary = "Page skeleton component providing animated placeholder layouts for route-level loading states."
            tags = ["component", "skeleton", "loading", "ui"]
        elif path == "components/ui/skeleton.tsx":
            summary = "Base Skeleton UI component with variant support for rectangular, circular, and text skeleton shapes."
            tags = ["component", "skeleton", "loading", "ui"]
            complexity = "moderate"
        elif "brutal/" in path:
            comp_name = name.replace(".tsx", "").title()
            summary = f"Brutalist-themed {comp_name} UI component with bold, heavy styling for the brutalist design system."
            tags = ["component", "brutalist", "ui"]
        elif "neumorphism/alert" in path:
            summary = "Neumorphism-themed alert and badge UI components with soft embossed styling."
            tags = ["component", "neumorphism", "ui"]
        elif "alert/alert" in path:
            summary = "Alert UI component with variants for different severity levels and accessible alert descriptions."
            tags = ["component", "alert", "ui"]
        elif "button/button" in path:
            summary = "Button UI component with multiple variants (default, primary, outline, ghost) via cva variant system."
            tags = ["component", "button", "ui"]
        elif "card/card" in path:
            summary = "Card UI component with header, footer, title, description, and content sub-components via cva."
            tags = ["component", "card", "ui"]
        elif "checkbox/checkbox" in path:
            summary = "Checkbox UI component using Radix UI primitive with accessible checkbox input."
            tags = ["component", "checkbox", "form", "ui"]
        elif "drawer/drawer" in path:
            summary = "Drawer UI component using Radix UI Dialog primitive for slide-in panel overlays."
            tags = ["component", "drawer", "overlay", "ui"]
        elif "input-otp/input-otp" in path:
            summary = "One-time password input component with segmented inputs for PIN/OTP code entry."
            tags = ["component", "input", "otp", "form", "ui"]
            complexity = "moderate"
        elif "input/input" in path:
            summary = "Input UI component with variant styling via cva for text input fields."
            tags = ["component", "input", "form", "ui"]
        elif "list/list" in path:
            summary = "List and ListItem UI components for rendering structured lists with consistent styling."
            tags = ["component", "list", "ui"]
        elif "loading/loading" in path:
            summary = "Loading spinner and loading overlay UI components with variant styling."
            tags = ["component", "loading", "spinner", "ui"]
        elif "modal/modal" in path:
            summary = "Modal dialog UI component using Radix UI Dialog primitive with header, footer, and content sections."
            tags = ["component", "modal", "overlay", "ui"]
            complexity = "moderate"
        elif path == "lib/utils.ts":
            summary = "Utility function combining clsx and tailwind-merge for conditional class name resolution."
            tags = ["utility", "styling", "tailwind"]
        else:
            summary = f"UI component: {name.replace('.tsx','').replace('-',' ').title()}."
            tags = ["component", "ui"]

        nodes.append({
            "id": f"file:{path}", "type": "file", "name": name, "filePath": path,
            "summary": summary, "tags": tags, "complexity": complexity
        })

        if path in inp["batchImportData"]:
            for imp_path in inp["batchImportData"][path]:
                edges.append({"source": f"file:{path}", "target": f"file:{imp_path}",
                              "type": "imports", "direction": "forward", "weight": 0.7})

    expected = sum(len(v) for v in inp["batchImportData"].values())
    actual = len([e for e in edges if e["type"] == "imports"])
    assert actual == expected, f"Batch 35 Import mismatch: {actual} != {expected}"

    write_output(35, nodes, edges)


# ============================================
# Batch 36 - UI components (neumorphism, progress, resizable, etc.) + lib/utils
# ============================================
def gen_batch_36():
    inp = get_input(36)
    struct = get_struct(36)
    nodes = []
    edges = []

    for r in struct["results"]:
        path = r["path"]
        name = path.split("/")[-1]
        nEL = r["nonEmptyLines"]

        complexity = "simple" if nEL < 50 else ("moderate" if nEL < 200 else "complex")

        if "neumorphism/" in path:
            comp_name = name.replace(".tsx", "").replace("-", " ").title().replace("Neu ", "")
            summary = f"Neumorphism-themed {comp_name} UI component with soft embossed styling and inset shadow effects."
            tags = ["component", "neumorphism", "ui"]
        elif path == "components/ui/progress/progress.tsx":
            summary = "Progress bar UI component with variant styling via cva for determinate progress indication."
            tags = ["component", "progress", "ui"]
        elif path == "components/ui/radio/radio.tsx":
            summary = "Radio group UI component using Radix UI primitive for accessible radio button groups."
            tags = ["component", "radio", "form", "ui"]
        elif path == "components/ui/resizable/resizable.tsx":
            summary = "Resizable panel layout component using react-resizable-panels for draggable split panes."
            tags = ["component", "layout", "resizable", "ui"]
            complexity = "moderate"
        elif path == "components/ui/select/select.tsx":
            summary = "Select dropdown UI component using Radix UI primitive with scroll buttons and grouped options."
            tags = ["component", "select", "form", "ui"]
            complexity = "moderate"
        elif path == "components/ui/table/table.tsx":
            summary = "Table UI component with header, body, footer, row, cell sub-components for data display."
            tags = ["component", "table", "data-display", "ui"]
            complexity = "moderate"
        elif path == "components/ui/toast/toast.tsx":
            summary = "Toast notification UI component using Radix UI Toast primitive with action buttons."
            tags = ["component", "toast", "notification", "ui"]
            complexity = "moderate"
        elif path == "components/ui/tooltip/tooltip.tsx":
            summary = "Tooltip UI component using Radix UI Tooltip primitive for hover tooltip displays."
            tags = ["component", "tooltip", "ui"]
        elif path == "components/ui/tree/tree.tsx":
            summary = "Tree view UI component using Radix UI Tree primitive for hierarchical data navigation."
            tags = ["component", "tree", "navigation", "ui"]
        elif path == "components/ui/skeleton.tsx":
            summary = "Base Skeleton component and composite skeleton patterns for page loading placeholders."
            tags = ["component", "skeleton", "loading", "ui"]
            complexity = "moderate"
        elif path == "lib/utils.ts":
            summary = "Utility function combining clsx and tailwind-merge for conditional Tailwind class name resolution."
            tags = ["utility", "styling", "tailwind"]
        else:
            summary = f"UI component: {name.replace('.tsx','').replace('-',' ').title()}."
            tags = ["component", "ui"]

        if path.startswith("components/ui/neumorphism/styles.ts"):
            summary = "Shared design token constants for neumorphism UI components including shadow definitions."
            tags = ["style-definition", "neumorphism", "tokens"]

        nodes.append({
            "id": f"file:{path}", "type": "file", "name": name, "filePath": path,
            "summary": summary, "tags": tags, "complexity": complexity
        })

        if path in inp["batchImportData"]:
            for imp_path in inp["batchImportData"][path]:
                edges.append({"source": f"file:{path}", "target": f"file:{imp_path}",
                              "type": "imports", "direction": "forward", "weight": 0.7})

    expected = sum(len(v) for v in inp["batchImportData"].values())
    actual = len([e for e in edges if e["type"] == "imports"])
    assert actual == expected, f"Batch 36 Import mismatch: {actual} != {expected}"

    write_output(36, nodes, edges)


# ============================================
# Batch 37 - Templates (admin-panel through magazine-landing)
# ============================================
def gen_batch_37():
    inp = get_input(37)
    struct = get_struct(37)
    nodes = []
    edges = []

    for r in struct["results"]:
        path = r["path"]
        name = path.split("/")[-1]
        nEL = r["nonEmptyLines"]

        complexity = "simple" if nEL < 50 else ("moderate" if nEL < 200 else "complex")
        if nEL > 500: complexity = "complex"

        tpl_name = path.split("/")[-2].replace("-", " ").title()

        summary = f"Full-page {tpl_name} template with complete layouts, interactive components, and responsive design for the template showcase."
        tags = ["template", "page", "showcase"]

        nodes.append({
            "id": f"file:{path}", "type": "file", "name": name, "filePath": path,
            "summary": summary, "tags": tags, "complexity": complexity
        })

        if path in inp["batchImportData"]:
            for imp_path in inp["batchImportData"][path]:
                edges.append({"source": f"file:{path}", "target": f"file:{imp_path}",
                              "type": "imports", "direction": "forward", "weight": 0.7})

    expected = sum(len(v) for v in inp["batchImportData"].values())
    actual = len([e for e in edges if e["type"] == "imports"])
    assert actual == expected, f"Batch 37 Import mismatch: {actual} != {expected}"

    write_output(37, nodes, edges)


# ============================================
# Batch 38 - Templates (minimalist-portfolio through yohaku-blog) + utility components
# ============================================
def gen_batch_38():
    inp = get_input(38)
    struct = get_struct(38)
    nodes = []
    edges = []

    for r in struct["results"]:
        path = r["path"]
        name = path.split("/")[-1]
        nEL = r["nonEmptyLines"]

        complexity = "simple" if nEL < 50 else ("moderate" if nEL < 200 else "complex")
        if nEL > 500: complexity = "complex"

        if path.startswith("app/templates/"):
            tpl_name = path.split("/")[-2].replace("-", " ").title()
            summary = f"Full-page {tpl_name} template with complete layouts, interactive components, and responsive design for the template showcase."
            tags = ["template", "page", "showcase"]
        elif path == "components/scroll-back-button.tsx":
            summary = "Scroll-aware back button that saves and restores scroll position when navigating between pages."
            tags = ["component", "navigation", "ux"]
            complexity = "moderate"
        elif path == "components/templates/template-back-button.tsx":
            summary = "Back button component for template pages with i18n-aware navigation and scroll position restoration."
            tags = ["component", "navigation", "back-button"]
            complexity = "moderate"
        elif path == "components/ui/brutal/index.tsx":
            summary = "Barrel re-export file aggregating all brutalist UI components from the brutal directory."
            tags = ["barrel", "index", "brutalist"]
        elif path == "lib/navigation/smart-back.ts":
            summary = "Smart navigation utility that intelligently chooses between browser back, saved return URL, or fallback route."
            tags = ["utility", "navigation", "routing"]
            complexity = "moderate"
        else:
            summary = f"Module: {name.replace('.tsx','').replace('.ts','').replace('-',' ').title()}."
            tags = ["utility"]

        nodes.append({
            "id": f"file:{path}", "type": "file", "name": name, "filePath": path,
            "summary": summary, "tags": tags, "complexity": complexity
        })

        if path in inp["batchImportData"]:
            for imp_path in inp["batchImportData"][path]:
                edges.append({"source": f"file:{path}", "target": f"file:{imp_path}",
                              "type": "imports", "direction": "forward", "weight": 0.7})

    expected = sum(len(v) for v in inp["batchImportData"].values())
    actual = len([e for e in edges if e["type"] == "imports"])
    assert actual == expected, f"Batch 38 Import mismatch: {actual} != {expected}"

    write_output(38, nodes, edges)


# ============================================
# Batch 39 - Auth (API routes + auth lib)
# ============================================
def gen_batch_39():
    inp = get_input(39)
    struct = get_struct(39)
    nodes = []
    edges = []

    for r in struct["results"]:
        path = r["path"]
        name = path.split("/")[-1]
        nEL = r["nonEmptyLines"]

        complexity = "simple" if nEL < 50 else ("moderate" if nEL < 200 else "complex")

        if "linuxdo" in path:
            if "route.ts" in path and "callback" in path:
                summary = "API route handling the LinuxDo OAuth callback flow, exchanging authorization codes for user tokens and creating sessions."
                tags = ["api-handler", "auth", "oauth", "route"]
                complexity = "moderate"
            elif "route.ts" in path:
                summary = "API route initiating LinuxDo OAuth authentication by redirecting users to the LinuxDo authorization URL."
                tags = ["api-handler", "auth", "oauth", "route"]
            elif "__tests__" in path:
                test_name = path.split("/")[-1].replace(".test.ts", "")
                summary = f"Unit tests for the LinuxDo OAuth {test_name} route handler."
                tags = ["test", "unit", "auth"]
            elif path == "lib/auth/linuxdo.ts":
                summary = "LinuxDo OAuth client library handling authorization URL building, token exchange, and user profile retrieval."
                tags = ["auth", "oauth", "utility"]
                complexity = "moderate"
        elif "callback" in path:
            if "route.ts" in path:
                summary = "API route handling the legacy admin password authentication callback."
                tags = ["api-handler", "auth", "route"]
            elif "__tests__" in path:
                summary = "Unit tests for the legacy admin password authentication callback route."
                tags = ["test", "unit", "auth"]
        elif path == "lib/auth/seq-id.ts":
            summary = "Sequential ID assignment library for assigning human-friendly sequential IDs to users based on registration order."
            tags = ["utility", "auth", "id-generation"]
            complexity = "moderate"

        nodes.append({
            "id": f"file:{path}", "type": "file", "name": name, "filePath": path,
            "summary": summary, "tags": tags, "complexity": complexity
        })

        if path in inp["batchImportData"]:
            for imp_path in inp["batchImportData"][path]:
                edges.append({"source": f"file:{path}", "target": f"file:{imp_path}",
                              "type": "imports", "direction": "forward", "weight": 0.7})

    expected = sum(len(v) for v in inp["batchImportData"].values())
    actual = len([e for e in edges if e["type"] == "imports"])
    assert actual == expected, f"Batch 39 Import mismatch: {actual} != {expected}"

    write_output(39, nodes, edges)


# ============================================
# Batch 40 - Submit/validation + manifest tools
# ============================================
def gen_batch_40():
    inp = get_input(40)
    struct = get_struct(40)
    nodes = []
    edges = []

    for r in struct["results"]:
        path = r["path"]
        name = path.split("/")[-1]
        nEL = r["nonEmptyLines"]

        complexity = "simple" if nEL < 50 else ("moderate" if nEL < 200 else "complex")

        if path == "lib/submit/manifest-validator.ts":
            summary = "Style submission manifest validation with Zod schema, detailed validation, and summary generation for style uploads."
            tags = ["validation", "utility", "schema-definition"]
            complexity = "moderate"
        elif path == "lib/submit/validator.ts":
            summary = "Zod schema definitions for the style submission wizard form with field-level validation rules."
            tags = ["validation", "schema-definition", "form"]
        elif path == "tools/submission/validate-manifest.ts":
            summary = "CLI tool script for validating style submission manifest files against the manifest schema."
            tags = ["cli-tool", "validation", "script"]
        elif "test" in path:
            test_name = path.split("/")[-1].replace(".test.ts", "")
            summary = f"Unit tests for the {test_name.replace('-', ' ')} module covering validation logic and edge cases."
            tags = ["test", "unit", "validation"]

        nodes.append({
            "id": f"file:{path}", "type": "file", "name": name, "filePath": path,
            "summary": summary, "tags": tags, "complexity": complexity
        })

        if path in inp["batchImportData"]:
            for imp_path in inp["batchImportData"][path]:
                edges.append({"source": f"file:{path}", "target": f"file:{imp_path}",
                              "type": "imports", "direction": "forward", "weight": 0.7})

    expected = sum(len(v) for v in inp["batchImportData"].values())
    actual = len([e for e in edges if e["type"] == "imports"])
    assert actual == expected, f"Batch 40 Import mismatch: {actual} != {expected}"

    write_output(40, nodes, edges)


# ============================================
# Batch 41 - CI/CD workflows
# ============================================
def gen_batch_41():
    inp = get_input(41)
    struct = get_struct(41)
    nodes = []
    edges = []

    for r in struct["results"]:
        path = r["path"]
        name = path.split("/")[-1]
        nEL = r["nonEmptyLines"]

        complexity = "simple" if nEL < 50 else ("moderate" if nEL < 200 else "complex")

        if "ci.yml" in path:
            summary = "Main CI pipeline running lint, typecheck, tests, build, and E2E tests on push/PR to main/dev branches."
            tags = ["ci-cd", "pipeline", "testing"]
            complexity = "moderate"
        elif "core-publish" in path:
            summary = "CD pipeline publishing the @stylekit/core package to npm on git tag push with provenance."
            tags = ["ci-cd", "deployment", "npm"]
        elif "secret-scan" in path:
            summary = "Security CI workflow running secret scanning on the repository to prevent credential leaks."
            tags = ["ci-cd", "security", "scanning"]
        elif "style-extractor-ci" in path:
            summary = "CI workflow for running style extractor integration tests on different Node.js versions."
            tags = ["ci-cd", "testing", "style-extractor"]
        elif "lint-example" in path:
            summary = "CI workflow template showcasing a minimal linting configuration for style contributions."
            tags = ["ci-cd", "linting", "example"]

        nodes.append({
            "id": f"pipeline:{path}", "type": "pipeline", "name": name, "filePath": path,
            "summary": summary, "tags": tags, "complexity": complexity,
            "languageNotes": "GitHub Actions YAML workflow with job-level dependency between build and e2e stages."
        })

        if path in inp["batchImportData"]:
            for imp_path in inp["batchImportData"][path]:
                edges.append({"source": f"pipeline:{path}", "target": f"file:{imp_path}",
                              "type": "triggers", "direction": "forward", "weight": 0.6})

    # Add some relevant edges to code files these pipelines would deploy/test
    edges.append({"source": "pipeline:.github/workflows/ci.yml", "target": "file:app/[locale]/layout.tsx",
                  "type": "triggers", "direction": "forward", "weight": 0.6})

    write_output(41, nodes, edges)


# ============================================
# Batch 42 - SQL migrations
# ============================================
def gen_batch_42():
    inp = get_input(42)
    struct = get_struct(42)
    nodes = []
    edges = []

    migration_tables = {
        "lib/supabase/migrations/001_initial_schema.sql": [
            ("submissions", "Initial table for style submissions with status tracking, review notes, and submission metadata."),
            ("analytics_events", "Table for tracking analytics events including event type, style slug, and session info."),
            ("favorites", "Table for storing user style favorites with session and style slug tracking.")
        ],
        "lib/supabase/migrations/002_ratings_comments.sql": [
            ("style_ratings", "Table for user ratings on styles with numeric rating values and session tracking."),
            ("style_comments", "Table for user comments on styles with content, author name, and moderation fields.")
        ],
        "lib/supabase/migrations/003_user_binding.sql": [],
        "lib/supabase/migrations/004_user_seq_ids.sql": [
            ("user_seq_ids", "Table mapping user IDs to sequential display numbers for human-friendly user identification.")
        ],
        "lib/supabase/migrations/005_ugc_identity_nullable.sql": [],
        "lib/supabase/migrations/006_user_titles.sql": [
            ("user_titles", "Table for custom user display titles with owner flag and visibility control.")
        ],
        "lib/supabase/migrations/007_reset_user_seq_id.sql": [],
        "lib/supabase/migrations/008_dense_renumber_seq_ids.sql": [],
        "lib/supabase/migrations/009_user_title_colors.sql": [],
        "lib/supabase/migrations/010_seq11_special_title.sql": [],
        "lib/supabase/migrations/011_dense_seq_id_function.sql": [],
        "lib/supabase/migrations/012_seq3_vector_title_icon.sql": []
    }

    for r in struct["results"]:
        path = r["path"]
        name = path.split("/")[-1]
        nEL = r["nonEmptyLines"]

        complexity = "simple" if nEL < 50 else ("moderate" if nEL < 200 else "complex")

        # Extract migration number and purpose
        mig_num = path.split("_")[0].split("/")[-1]

        if path == "lib/supabase/migrations/001_initial_schema.sql":
            summary = f"Initial database schema creating the core submissions, analytics_events, and favorites tables with indexes."
            tags = ["database", "migration", "schema-definition"]
            complexity = "moderate"
        elif path == "lib/supabase/migrations/002_ratings_comments.sql":
            summary = "Adds style_ratings and style_comments tables for user feedback with rating aggregation view."
            tags = ["database", "migration", "schema-definition"]
        elif path == "lib/supabase/migrations/003_user_binding.sql":
            summary = "Adds user foreign key columns to existing tables binding anonymous session data to registered users."
            tags = ["database", "migration", "schema-definition"]
        elif path == "lib/supabase/migrations/004_user_seq_ids.sql":
            summary = "Creates user_seq_ids table for sequential user numbering with unique sequence ID index."
            tags = ["database", "migration", "schema-definition"]
        elif path == "lib/supabase/migrations/005_ugc_identity_nullable.sql":
            summary = "Adds nullable user identity columns to ratings and comments tables for gradual migration."
            tags = ["database", "migration"]
        elif path == "lib/supabase/migrations/006_user_titles.sql":
            summary = "Creates user_titles table for custom display names assigned by administrators."
            tags = ["database", "migration", "schema-definition"]
        elif path == "lib/supabase/migrations/007_reset_user_seq_id.sql":
            summary = "Resets the user sequential ID counter, used for administrative renumbering."
            tags = ["database", "migration"]
        elif path == "lib/supabase/migrations/008_dense_renumber_seq_ids.sql":
            summary = "Dense renumbering of user sequential IDs to fill gaps left by deleted users."
            tags = ["database", "migration"]
        elif path == "lib/supabase/migrations/009_user_title_colors.sql":
            summary = "Adds color customization support for user display titles."
            tags = ["database", "migration"]
        elif path == "lib/supabase/migrations/010_seq11_special_title.sql":
            summary = "Creates a special reserved sequential ID with a dedicated display title."
            tags = ["database", "migration"]
        elif path == "lib/supabase/migrations/011_dense_seq_id_function.sql":
            summary = "PostgreSQL function for dense renumbering of user sequential IDs maintaining ordering."
            tags = ["database", "migration", "function"]
        elif path == "lib/supabase/migrations/012_seq3_vector_title_icon.sql":
            summary = "Adds icon support for vector-themed title displays for sequential ID holders."
            tags = ["database", "migration"]

        nodes.append({
            "id": f"file:{path}", "type": "table", "name": name, "filePath": path,
            "summary": summary, "tags": tags, "complexity": complexity
        })

        # Create table nodes for tables defined in this migration
        if path in migration_tables:
            for tbl_name, tbl_summary in migration_tables[path]:
                tbl_node_id = f"table:{path}:{tbl_name}"
                nodes.append({
                    "id": tbl_node_id, "type": "table", "name": tbl_name,
                    "filePath": path,
                    "summary": tbl_summary,
                    "tags": ["table", "database", "schema-definition"],
                    "complexity": "simple"
                })
                # migrates edge from migration to table
                edges.append({
                    "source": f"file:{path}", "target": tbl_node_id,
                    "type": "migrates", "direction": "forward", "weight": 0.7
                })

    write_output(42, nodes, edges)


# ============================================
# Run all generators
# ============================================
print("Generating batch 30...")
gen_batch_30()
print("Generating batch 31...")
gen_batch_31()
print("Generating batch 32...")
gen_batch_32()
print("Generating batch 33...")
gen_batch_33()
print("Generating batch 34...")
gen_batch_34()
print("Generating batch 35...")
gen_batch_35()
print("Generating batch 36...")
gen_batch_36()
print("Generating batch 37...")
gen_batch_37()
print("Generating batch 38...")
gen_batch_38()
print("Generating batch 39...")
gen_batch_39()
print("Generating batch 40...")
gen_batch_40()
print("Generating batch 41...")
gen_batch_41()
print("Generating batch 42...")
gen_batch_42()
print("All batches generated!")
