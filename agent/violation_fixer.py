"""
Violation Fix Generator

Analyzes axe-core violations and generates exact code snippets with fixes.
Provides before/after code comparison for developers to copy-paste directly.
"""

import re
from typing import Dict, List, Optional, Tuple


class ViolationFixer:
    """Generates exact code fixes for accessibility violations."""
    
    def __init__(self):
        """Initialize the violation fixer with rule-based fix patterns."""
        self.fix_patterns = self._build_fix_patterns()
    
    def _build_fix_patterns(self) -> Dict[str, Dict]:
        """
        Build rule-based fix patterns for common violations.
        
        Returns:
            Dictionary mapping violation IDs to fix strategies
        """
        return {
            # ========== Form Controls ==========
            'button-name': {
                'description': 'Buttons must have discernible text',
                'detection': lambda html: '<button' in html and not any(x in html for x in ['aria-label=', '>']) or html.strip().endswith('</button>'),
                'fix': self._fix_button_name
            },
            'label': {
                'description': 'Form elements must have labels',
                'detection': lambda html: '<input' in html and 'type=' in html,
                'fix': self._fix_input_label
            },
            'input-button-name': {
                'description': 'Input buttons must have discernible text',
                'detection': lambda html: '<input' in html and 'type="button"' in html,
                'fix': self._fix_input_button_name
            },
            
            # ========== Images ==========
            'image-alt': {
                'description': 'Images must have alternate text',
                'detection': lambda html: '<img' in html,
                'fix': self._fix_image_alt
            },
            'image-redundant-alt': {
                'description': 'Image alt text should not be redundant',
                'detection': lambda html: '<img' in html and 'alt=' in html,
                'fix': self._fix_redundant_alt
            },
            
            # ========== Links ==========
            'link-name': {
                'description': 'Links must have discernible text',
                'detection': lambda html: '<a' in html and 'href=' in html,
                'fix': self._fix_link_name
            },
            
            # ========== Color Contrast ==========
            'color-contrast': {
                'description': 'Text must have sufficient contrast',
                'detection': lambda html: True,  # Need to extract computed colors
                'fix': self._fix_color_contrast
            },
            
            # ========== ARIA ==========
            'aria-required-attr': {
                'description': 'ARIA attributes must be present',
                'detection': lambda html: 'role=' in html,
                'fix': self._fix_aria_required_attr
            },
            'aria-valid-attr-value': {
                'description': 'ARIA attribute values must be valid',
                'detection': lambda html: 'aria-' in html,
                'fix': self._fix_aria_valid_attr
            },
            
            # ========== Headings ==========
            'heading-order': {
                'description': 'Heading levels should only increase by one',
                'detection': lambda html: re.search(r'<h[1-6]', html, re.IGNORECASE),
                'fix': self._fix_heading_order
            },
            
            # ========== Lists ==========
            'listitem': {
                'description': 'List items must be contained in lists',
                'detection': lambda html: '<li' in html,
                'fix': self._fix_listitem
            },
            
            # ========== Landmarks ==========
            'region': {
                'description': 'Content not in a landmark region',
                'detection': lambda html: True,
                'fix': self._fix_region
            },
            'landmark-one-main': {
                'description': 'Document should have one main landmark',
                'detection': lambda html: '<html' in html,
                'fix': self._fix_landmark_one_main
            },
            'landmark-banner-is-top-level': {
                'description': 'Banner landmark should not be contained in another landmark',
                'detection': lambda html: '<header' in html or 'role="banner"' in html,
                'fix': self._fix_landmark_banner_top_level
            },
            'landmark-contentinfo-is-top-level': {
                'description': 'Contentinfo landmark should not be contained in another landmark',
                'detection': lambda html: '<footer' in html or 'role="contentinfo"' in html,
                'fix': self._fix_landmark_contentinfo_top_level
            },
            'landmark-no-duplicate-banner': {
                'description': 'Document should not have more than one banner landmark',
                'detection': lambda html: '<header' in html or 'role="banner"' in html,
                'fix': self._fix_landmark_no_duplicate_banner
            },
            'landmark-no-duplicate-contentinfo': {
                'description': 'Document should not have more than one contentinfo landmark',
                'detection': lambda html: '<footer' in html or 'role="contentinfo"' in html,
                'fix': self._fix_landmark_no_duplicate_contentinfo
            },
            'landmark-unique': {
                'description': 'Ensures landmarks are unique',
                'detection': lambda html: 'role=' in html or any(tag in html for tag in ['<header', '<footer', '<nav', '<main', '<aside']),
                'fix': self._fix_landmark_unique
            },
            
            # ========== IDs ==========
            'duplicate-id-active': {
                'description': 'Ensures every id attribute value of active elements is unique',
                'detection': lambda html: 'id=' in html,
                'fix': self._fix_duplicate_id
            },
            'duplicate-id': {
                'description': 'Ensures every id attribute value is unique',
                'detection': lambda html: 'id=' in html,
                'fix': self._fix_duplicate_id
            },
            'duplicate-id-aria': {
                'description': 'Ensures every id attribute value used in ARIA is unique',
                'detection': lambda html: 'id=' in html,
                'fix': self._fix_duplicate_id
            },
            
            # ========== Additional ARIA Rules ==========
            'aria-allowed-attr': {
                'description': 'ARIA attributes must be appropriate for element role',
                'detection': lambda html: 'aria-' in html and 'role=' in html,
                'fix': self._fix_aria_allowed_attr
            },
            'aria-hidden-focus': {
                'description': 'aria-hidden elements must not contain focusable elements',
                'detection': lambda html: 'aria-hidden' in html,
                'fix': self._fix_aria_hidden_focus
            },
            'aria-input-field-name': {
                'description': 'ARIA input fields must have accessible names',
                'detection': lambda html: '<input' in html or 'role="textbox"' in html,
                'fix': self._fix_aria_input_field_name
            },
            'aria-required-children': {
                'description': 'ARIA roles must contain required child roles',
                'detection': lambda html: 'role=' in html,
                'fix': self._fix_aria_required_children
            },
            'aria-required-parent': {
                'description': 'ARIA roles must be contained by required parent roles',
                'detection': lambda html: 'role=' in html,
                'fix': self._fix_aria_required_parent
            },
            'aria-roles': {
                'description': 'ARIA role values must be valid',
                'detection': lambda html: 'role=' in html,
                'fix': self._fix_aria_roles
            },
            'aria-toggle-field-name': {
                'description': 'ARIA toggle fields must have accessible names',
                'detection': lambda html: 'role="switch"' in html or 'role="checkbox"' in html,
                'fix': self._fix_aria_toggle_field_name
            },
            
            # ========== Form Controls (Extended) ==========
            'autocomplete-valid': {
                'description': 'autocomplete attribute must have valid value',
                'detection': lambda html: 'autocomplete=' in html,
                'fix': self._fix_autocomplete_valid
            },
            'select-name': {
                'description': 'Select elements must have accessible names',
                'detection': lambda html: '<select' in html,
                'fix': self._fix_select_name
            },
            'form-field-multiple-labels': {
                'description': 'Form fields should not have multiple label elements',
                'detection': lambda html: '<input' in html or '<select' in html or '<textarea' in html,
                'fix': self._fix_form_field_multiple_labels
            },
            
            # ========== Document Structure ==========
            'bypass': {
                'description': 'Page must have mechanism to bypass repeated content',
                'detection': lambda html: '<body' in html,
                'fix': self._fix_bypass
            },
            'document-title': {
                'description': 'Documents must have title element',
                'detection': lambda html: '<head' in html,
                'fix': self._fix_document_title
            },
            'html-has-lang': {
                'description': 'html element must have lang attribute',
                'detection': lambda html: '<html' in html,
                'fix': self._fix_html_has_lang
            },
            'html-lang-valid': {
                'description': 'html lang attribute must have valid value',
                'detection': lambda html: '<html' in html and 'lang=' in html,
                'fix': self._fix_html_lang_valid
            },
            'html-xml-lang-mismatch': {
                'description': 'xml:lang and lang attributes must match',
                'detection': lambda html: '<html' in html and 'xml:lang=' in html,
                'fix': self._fix_html_xml_lang_mismatch
            },
            'valid-lang': {
                'description': 'lang attribute must have valid value',
                'detection': lambda html: 'lang=' in html,
                'fix': self._fix_valid_lang
            },
            
            # ========== Lists (Extended) ==========
            'definition-list': {
                'description': 'dl elements must only contain dt and dd elements',
                'detection': lambda html: '<dl' in html,
                'fix': self._fix_definition_list
            },
            'dlitem': {
                'description': 'dt and dd elements must be contained within dl',
                'detection': lambda html: '<dt' in html or '<dd' in html,
                'fix': self._fix_dlitem
            },
            
            # ========== Headings (Extended) ==========
            'empty-heading': {
                'description': 'Headings must not be empty',
                'detection': lambda html: re.search(r'<h[1-6]', html, re.IGNORECASE),
                'fix': self._fix_empty_heading
            },
            
            # ========== Frames ==========
            'frame-title': {
                'description': 'Frames and iframes must have title attribute',
                'detection': lambda html: '<iframe' in html or '<frame' in html,
                'fix': self._fix_frame_title
            },
            
            # ========== Meta Tags ==========
            'meta-refresh': {
                'description': 'Timed refresh must not exist',
                'detection': lambda html: '<meta' in html and 'http-equiv' in html,
                'fix': self._fix_meta_refresh
            },
            'meta-viewport': {
                'description': 'Zooming and scaling must not be disabled',
                'detection': lambda html: '<meta' in html and 'viewport' in html,
                'fix': self._fix_meta_viewport
            },
            
            # ========== Multimedia ==========
            'object-alt': {
                'description': 'object elements must have alternative text',
                'detection': lambda html: '<object' in html,
                'fix': self._fix_object_alt
            },
            'svg-img-alt': {
                'description': 'SVG elements with img role must have alternative text',
                'detection': lambda html: '<svg' in html and 'role="img"' in html,
                'fix': self._fix_svg_img_alt
            },
            'role-img-alt': {
                'description': 'Elements with role=img must have alternative text',
                'detection': lambda html: 'role="img"' in html,
                'fix': self._fix_role_img_alt
            },
            'video-caption': {
                'description': 'video elements must have captions',
                'detection': lambda html: '<video' in html,
                'fix': self._fix_video_caption
            },
            'audio-caption': {
                'description': 'audio elements must have captions or transcripts',
                'detection': lambda html: '<audio' in html,
                'fix': self._fix_audio_caption
            },
            
            # ========== Tables ==========
            'table-duplicate-name': {
                'description': 'Tables should not have the same summary and caption',
                'detection': lambda html: '<table' in html,
                'fix': self._fix_table_duplicate_name
            },
            'td-headers-attr': {
                'description': 'td headers attribute must refer to table headers',
                'detection': lambda html: '<td' in html and 'headers=' in html,
                'fix': self._fix_td_headers_attr
            },
            'th-has-data-cells': {
                'description': 'th elements must have data cells they describe',
                'detection': lambda html: '<th' in html,
                'fix': self._fix_th_has_data_cells
            },
            
            # ========== Keyboard/Focus ==========
            'tabindex': {
                'description': 'tabindex value must not be greater than 0',
                'detection': lambda html: 'tabindex=' in html,
                'fix': self._fix_tabindex
            },
            'scrollable-region-focusable': {
                'description': 'Scrollable regions must be keyboard accessible',
                'detection': lambda html: 'overflow' in html or 'scroll' in html,
                'fix': self._fix_scrollable_region_focusable
            },
            
            # ========== ADDITIONAL ARIA RULES (15 more) ==========
            'aria-allowed-role': {
                'description': 'ARIA role must be appropriate for the element',
                'detection': lambda html: 'role=' in html,
                'fix': self._fix_aria_allowed_role
            },
            'aria-command-name': {
                'description': 'ARIA commands must have accessible names',
                'detection': lambda html: 'role="button"' in html or 'role="link"' in html or 'role="menuitem"' in html,
                'fix': self._fix_aria_command_name
            },
            'aria-dialog-name': {
                'description': 'ARIA dialog must have accessible name',
                'detection': lambda html: 'role="dialog"' in html or 'role="alertdialog"' in html,
                'fix': self._fix_aria_dialog_name
            },
            'aria-meter-name': {
                'description': 'ARIA meter must have accessible name',
                'detection': lambda html: 'role="meter"' in html,
                'fix': self._fix_aria_meter_name
            },
            'aria-progressbar-name': {
                'description': 'ARIA progressbar must have accessible name',
                'detection': lambda html: 'role="progressbar"' in html,
                'fix': self._fix_aria_progressbar_name
            },
            'aria-tooltip-name': {
                'description': 'ARIA tooltip must have accessible name',
                'detection': lambda html: 'role="tooltip"' in html,
                'fix': self._fix_aria_tooltip_name
            },
            'aria-treeitem-name': {
                'description': 'ARIA treeitem must have accessible name',
                'detection': lambda html: 'role="treeitem"' in html,
                'fix': self._fix_aria_treeitem_name
            },
            'aria-valid-attr': {
                'description': 'ARIA attributes must be valid',
                'detection': lambda html: 'aria-' in html,
                'fix': self._fix_aria_valid_attr
            },
            'aria-conditional-attr': {
                'description': 'ARIA attributes must be used as specified for element role',
                'detection': lambda html: 'aria-' in html and 'role=' in html,
                'fix': self._fix_aria_conditional_attr
            },
            'aria-deprecated-role': {
                'description': 'Deprecated ARIA roles must not be used',
                'detection': lambda html: 'role=' in html,
                'fix': self._fix_aria_deprecated_role
            },
            'aria-prohibited-attr': {
                'description': 'ARIA attributes must not be used on elements that prohibit them',
                'detection': lambda html: 'aria-' in html,
                'fix': self._fix_aria_prohibited_attr
            },
            'aria-text': {
                'description': 'role="text" must have no focusable descendants',
                'detection': lambda html: 'role="text"' in html,
                'fix': self._fix_aria_text
            },
            'aria-hidden-body': {
                'description': 'aria-hidden must not be present on body',
                'detection': lambda html: '<body' in html and 'aria-hidden' in html,
                'fix': self._fix_aria_hidden_body
            },
            
            # ========== ADDITIONAL FORM RULES (6 more) ==========
            'input-image-alt': {
                'description': 'Image buttons must have alternate text',
                'detection': lambda html: '<input' in html and 'type="image"' in html,
                'fix': self._fix_input_image_alt
            },
            'fieldset': {
                'description': 'Radio buttons and checkboxes must be in fieldset',
                'detection': lambda html: 'type="radio"' in html or 'type="checkbox"' in html,
                'fix': self._fix_fieldset
            },
            'label-title-only': {
                'description': 'Form elements should not rely solely on title attribute',
                'detection': lambda html: '<input' in html and 'title=' in html,
                'fix': self._fix_label_title_only
            },
            'label-content-name-mismatch': {
                'description': 'Label text must match or contain accessible name',
                'detection': lambda html: '<label' in html,
                'fix': self._fix_label_content_name_mismatch
            },
            
            # ========== ADDITIONAL LINK RULES (2 more) ==========
            'link-in-text-block': {
                'description': 'Links must be distinguished from surrounding text',
                'detection': lambda html: '<a' in html and 'href=' in html,
                'fix': self._fix_link_in_text_block
            },
            'identical-links-same-purpose': {
                'description': 'Identical links should serve similar purpose',
                'detection': lambda html: '<a' in html and 'href=' in html,
                'fix': self._fix_identical_links_same_purpose
            },
            
            # ========== ADDITIONAL COLOR & CONTRAST (1 more) ==========
            'color-contrast-enhanced': {
                'description': 'Text must have enhanced contrast (Level AAA)',
                'detection': lambda html: True,
                'fix': self._fix_color_contrast_enhanced
            },
            
            # ========== ADDITIONAL HEADING RULES (2 more) ==========
            'p-as-heading': {
                'description': 'Paragraphs should not be styled as headings',
                'detection': lambda html: '<p' in html,
                'fix': self._fix_p_as_heading
            },
            'page-has-heading-one': {
                'description': 'Page should contain a level-one heading',
                'detection': lambda html: '<h1' not in html,
                'fix': self._fix_page_has_heading_one
            },
            
            # ========== ADDITIONAL TABLE RULES (7 more) ==========
            'td-has-header': {
                'description': 'Data cells must have table headers',
                'detection': lambda html: '<td' in html,
                'fix': self._fix_td_has_header
            },
            'th-has-scope': {
                'description': 'th elements must have scope attribute',
                'detection': lambda html: '<th' in html,
                'fix': self._fix_th_has_scope
            },
            'scope-attr-valid': {
                'description': 'scope attribute must be valid',
                'detection': lambda html: 'scope=' in html,
                'fix': self._fix_scope_attr_valid
            },
            'table-fake-caption': {
                'description': 'Data tables should use caption element',
                'detection': lambda html: '<table' in html,
                'fix': self._fix_table_fake_caption
            },
            'layout-table': {
                'description': 'Layout tables must not use data table elements',
                'detection': lambda html: '<table' in html,
                'fix': self._fix_layout_table
            },
            'caption-faked': {
                'description': 'Table captions should use caption element',
                'detection': lambda html: '<table' in html,
                'fix': self._fix_caption_faked
            },
            'empty-table-header': {
                'description': 'Table headers must not be empty',
                'detection': lambda html: '<th' in html,
                'fix': self._fix_empty_table_header
            },
            
            # ========== ADDITIONAL LIST RULES (1 more) ==========
            'list': {
                'description': 'ul/ol must only contain li, script, or template elements',
                'detection': lambda html: '<ul' in html or '<ol' in html,
                'fix': self._fix_list
            },
            
            # ========== ADDITIONAL MULTIMEDIA RULES (4 more) ==========
            'iframe-title': {
                'description': 'iframe elements must have title attribute',
                'detection': lambda html: '<iframe' in html,
                'fix': self._fix_iframe_title
            },
            'area-alt': {
                'description': 'Active area elements must have alternate text',
                'detection': lambda html: '<area' in html,
                'fix': self._fix_area_alt
            },
            'blink': {
                'description': 'blink elements are deprecated and must not be used',
                'detection': lambda html: '<blink' in html,
                'fix': self._fix_blink
            },
            'marquee': {
                'description': 'marquee elements are deprecated and must not be used',
                'detection': lambda html: '<marquee' in html,
                'fix': self._fix_marquee
            },
            'server-side-image-map': {
                'description': 'Server-side image maps must not be used',
                'detection': lambda html: 'ismap' in html,
                'fix': self._fix_server_side_image_map
            },
            
            # ========== ADDITIONAL PAGE STRUCTURE (3 more) ==========
            'skip-link': {
                'description': 'Skip links must be focusable',
                'detection': lambda html: '<a' in html and '#' in html,
                'fix': self._fix_skip_link
            },
            'hidden-content': {
                'description': 'Hidden content should not be focusable',
                'detection': lambda html: 'display: none' in html or 'visibility: hidden' in html,
                'fix': self._fix_hidden_content
            },
            
            # ========== ADDITIONAL FOCUS & KEYBOARD (4 more) ==========
            'accesskeys': {
                'description': 'accesskey attribute values must be unique',
                'detection': lambda html: 'accesskey=' in html,
                'fix': self._fix_accesskeys
            },
            'focus-order-semantics': {
                'description': 'Focusable elements must have appropriate semantics',
                'detection': lambda html: 'tabindex=' in html,
                'fix': self._fix_focus_order_semantics
            },
            'focusable-no-name': {
                'description': 'Focusable elements must have accessible names',
                'detection': lambda html: 'tabindex=' in html or '<a' in html or '<button' in html,
                'fix': self._fix_focusable_no_name
            },
            'focusable-disabled': {
                'description': 'Disabled elements must not be focusable',
                'detection': lambda html: 'disabled' in html,
                'fix': self._fix_focusable_disabled
            },
            
            # ========== ADDITIONAL META & VIEWPORT (1 more) ==========
            'meta-viewport-large': {
                'description': 'Viewport meta must allow for zoom',
                'detection': lambda html: '<meta' in html and 'viewport' in html,
                'fix': self._fix_meta_viewport_large
            },
            
            # ========== ADVANCED WCAG (10 more) ==========
            'nested-interactive': {
                'description': 'Interactive controls must not be nested',
                'detection': lambda html: '<a' in html or '<button' in html,
                'fix': self._fix_nested_interactive
            },
            'no-autoplay-audio': {
                'description': 'Audio elements must not autoplay',
                'detection': lambda html: '<audio' in html or '<video' in html,
                'fix': self._fix_no_autoplay_audio
            },
            'css-orientation-lock': {
                'description': 'CSS must not lock display orientation',
                'detection': lambda html: 'transform' in html or '@media' in html,
                'fix': self._fix_css_orientation_lock
            },
            'avoid-inline-spacing': {
                'description': 'Inline text spacing must be adjustable',
                'detection': lambda html: 'style=' in html,
                'fix': self._fix_avoid_inline_spacing
            },
            'frame-tested': {
                'description': 'Frames must be tested for accessibility',
                'detection': lambda html: '<iframe' in html or '<frame' in html,
                'fix': self._fix_frame_tested
            },
            'presentation-role-conflict': {
                'description': 'Elements with presentation role must not have semantic children',
                'detection': lambda html: 'role="presentation"' in html or 'role="none"' in html,
                'fix': self._fix_presentation_role_conflict
            },
            'target-size': {
                'description': 'Touch targets must have sufficient size',
                'detection': lambda html: '<a' in html or '<button' in html,
                'fix': self._fix_target_size
            },
        }
    
    def generate_fix(self, violation: Dict, node: Dict) -> Optional[Dict]:
        """
        Generate a fix for a specific violation node.
        
        Args:
            violation: The violation object from axe-core
            node: The specific node with the violation
            
        Returns:
            Dictionary with 'before', 'after', 'explanation', 'steps' keys
            or None if no fix pattern available
        """
        violation_id = violation.get('id', '')
        html = node.get('html', '').strip()
        
        if not html:
            return None
        
        # Try rule-based fix first
        if violation_id in self.fix_patterns:
            pattern = self.fix_patterns[violation_id]
            try:
                return pattern['fix'](html, node, violation)
            except Exception as e:
                print(f"⚠️ Fix pattern failed for {violation_id}: {e}")
        
        # Fallback to generic fix based on violation message
        return self._generate_generic_fix(violation, node)
    
    # ==================== Fix Functions ====================
    
    def _fix_button_name(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix button with no accessible name."""
        # Extract button content if any
        content_match = re.search(r'<button[^>]*>(.*?)</button>', html, re.IGNORECASE | re.DOTALL)
        has_content = content_match and content_match.group(1).strip()
        
        # Check if it's an icon button
        is_icon_button = '<svg' in html or '<img' in html or 'icon' in html.lower()
        
        if is_icon_button:
            # Add aria-label for icon button
            fixed = re.sub(
                r'(<button)',
                r'\1 aria-label="[Describe button action]"',
                html,
                count=1,
                flags=re.IGNORECASE
            )
            explanation = "Icon buttons need aria-label to describe their action to screen readers"
            steps = [
                "Add aria-label with descriptive text (e.g., 'Close dialog', 'Submit form')",
                "If button contains decorative icon, add aria-hidden='true' to the icon"
            ]
        elif not has_content:
            # Add text content to empty button
            fixed = re.sub(
                r'(<button[^>]*>)\s*(</button>)',
                r'\1[Button Text]\2',
                html,
                flags=re.IGNORECASE
            )
            explanation = "Buttons must have visible text content or aria-label"
            steps = [
                "Add descriptive text inside the button tag",
                "Alternatively, add aria-label attribute with descriptive text"
            ]
        else:
            # Button has content but it's not accessible (maybe hidden)
            fixed = re.sub(
                r'(<button)',
                r'\1 aria-label="[Describe button purpose]"',
                html,
                count=1,
                flags=re.IGNORECASE
            )
            explanation = "Button content is not accessible - add aria-label as fallback"
            steps = [
                "Ensure button text is not hidden with CSS",
                "Add aria-label with descriptive text",
                "Remove aria-hidden from child elements"
            ]
        
        return {
            'before': html,
            'after': fixed,
            'explanation': explanation,
            'steps': steps,
            'wcag_criterion': '4.1.2 Name, Role, Value (Level A)',
            'impact': violation.get('impact', 'serious')
        }
    
    def _fix_input_label(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix input element missing label."""
        # Extract input attributes
        id_match = re.search(r'id=["\']([^"\']+)["\']', html)
        name_match = re.search(r'name=["\']([^"\']+)["\']', html)
        type_match = re.search(r'type=["\']([^"\']+)["\']', html)
        
        input_id = id_match.group(1) if id_match else 'input-field'
        input_name = name_match.group(1) if name_match else 'field'
        input_type = type_match.group(1) if type_match else 'text'
        
        # Generate label text from name or type
        label_text = input_name.replace('_', ' ').replace('-', ' ').title()
        
        # Ensure input has ID
        if not id_match:
            fixed_input = re.sub(
                r'(<input)',
                f'\\1 id="{input_id}"',
                html,
                count=1,
                flags=re.IGNORECASE
            )
        else:
            fixed_input = html
        
        # Add label element
        fixed = f'<label for="{input_id}">{label_text}</label>\n{fixed_input}'
        
        return {
            'before': html,
            'after': fixed,
            'explanation': f"Form inputs must have associated <label> elements for screen readers",
            'steps': [
                f"Add a <label> element with for='{input_id}' attribute",
                "Ensure input has matching id attribute",
                "Alternatively, wrap input inside <label> tags",
                "For invisible labels, use aria-label on the input"
            ],
            'wcag_criterion': '3.3.2 Labels or Instructions (Level A)',
            'impact': violation.get('impact', 'critical')
        }
    
    def _fix_input_button_name(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix input button with no value."""
        # Check if value attribute exists
        has_value = 'value=' in html
        
        if not has_value:
            fixed = re.sub(
                r'(<input[^>]*)',
                r'\1 value="[Button Text]"',
                html,
                flags=re.IGNORECASE
            )
            explanation = "Input buttons require a value attribute for their label"
        else:
            # Value is empty or whitespace
            fixed = re.sub(
                r'value=["\']["\']',
                r'value="[Button Text]"',
                html,
                flags=re.IGNORECASE
            )
            explanation = "Input button value cannot be empty"
        
        return {
            'before': html,
            'after': fixed,
            'explanation': explanation,
            'steps': [
                "Add value='[descriptive text]' attribute to input button",
                "Value should clearly describe the button's action"
            ],
            'wcag_criterion': '4.1.2 Name, Role, Value (Level A)',
            'impact': violation.get('impact', 'critical')
        }
    
    def _fix_image_alt(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix image with missing alt attribute."""
        # Extract src for context
        src_match = re.search(r'src=["\']([^"\']+)["\']', html)
        src = src_match.group(1) if src_match else ''
        
        # Determine if image is likely decorative
        is_decorative = any(keyword in src.lower() for keyword in ['icon', 'spacer', 'bullet', 'decoration'])
        
        if is_decorative:
            fixed = re.sub(
                r'(<img)',
                r'\1 alt=""',
                html,
                count=1,
                flags=re.IGNORECASE
            )
            explanation = "Decorative images should have alt='' to hide from screen readers"
            steps = [
                "Add alt='' (empty string) for purely decorative images",
                "Consider adding role='presentation' for clarity"
            ]
        else:
            fixed = re.sub(
                r'(<img)',
                r'\1 alt="[Describe the image content and purpose]"',
                html,
                count=1,
                flags=re.IGNORECASE
            )
            explanation = "All images must have alt text describing their content"
            steps = [
                "Add alt='[description]' with meaningful description",
                "Describe what the image shows and its purpose",
                "Keep alt text concise (under 150 characters)",
                "Don't use 'image of' or 'picture of' - screenreaders announce it's an image"
            ]
        
        return {
            'before': html,
            'after': fixed,
            'explanation': explanation,
            'steps': steps,
            'wcag_criterion': '1.1.1 Non-text Content (Level A)',
            'impact': violation.get('impact', 'critical')
        }
    
    def _fix_redundant_alt(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix image with redundant alt text."""
        # Extract current alt
        alt_match = re.search(r'alt=["\']([^"\']*)["\']', html)
        current_alt = alt_match.group(1) if alt_match else ''
        
        # Remove redundant words
        redundant_words = ['image', 'picture', 'photo', 'graphic', 'icon']
        cleaned_alt = current_alt
        for word in redundant_words:
            cleaned_alt = re.sub(rf'\b{word}\s+(of\s+)?', '', cleaned_alt, flags=re.IGNORECASE)
        
        cleaned_alt = cleaned_alt.strip() or '[Describe what the image shows]'
        
        fixed = re.sub(
            r'alt=["\'][^"\']*["\']',
            f'alt="{cleaned_alt}"',
            html,
            flags=re.IGNORECASE
        )
        
        return {
            'before': html,
            'after': fixed,
            'explanation': "Alt text should not include 'image', 'picture', etc. - screen readers already announce it's an image",
            'steps': [
                "Remove redundant words: 'image of', 'picture of', 'graphic of'",
                "Just describe what the image shows directly",
                f"Example: Change '{current_alt}' to '{cleaned_alt}'"
            ],
            'wcag_criterion': '1.1.1 Non-text Content (Level A)',
            'impact': violation.get('impact', 'minor')
        }
    
    def _fix_link_name(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix link with no accessible name."""
        # Check if link has text content
        content_match = re.search(r'<a[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
        has_content = content_match and content_match.group(1).strip()
        
        if not has_content or '<img' in html:
            # Icon link or empty link
            fixed = re.sub(
                r'(<a)',
                r'\1 aria-label="[Describe link destination]"',
                html,
                count=1,
                flags=re.IGNORECASE
            )
            explanation = "Links must have accessible text describing their destination"
            steps = [
                "Add aria-label describing where the link goes",
                "If link contains an image, ensure image has meaningful alt text",
                "For icon-only links, aria-label is required"
            ]
        else:
            # Link has content but might be hidden
            fixed = re.sub(
                r'(<a)',
                r'\1 aria-label="[Describe link destination]"',
                html,
                count=1,
                flags=re.IGNORECASE
            )
            explanation = "Link text is not accessible - ensure it's visible and descriptive"
            steps = [
                "Ensure link text is not hidden with CSS",
                "Use descriptive text instead of 'click here' or 'read more'",
                "Add aria-label if visible text is insufficient"
            ]
        
        return {
            'before': html,
            'after': fixed,
            'explanation': explanation,
            'steps': steps,
            'wcag_criterion': '4.1.2 Name, Role, Value (Level A)',
            'impact': violation.get('impact', 'serious')
        }
    
    def _fix_color_contrast(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix insufficient color contrast."""
        # Extract any foreground/background colors from node data
        fg_color = node.get('any', [{}])[0].get('data', {}).get('fgColor') if node.get('any') else None
        bg_color = node.get('any', [{}])[0].get('data', {}).get('bgColor') if node.get('any') else None
        
        # This is a CSS fix, not HTML fix
        explanation = "Text color contrast does not meet WCAG AA standards (4.5:1 for normal text, 3:1 for large text)"
        
        steps = [
            "Update CSS color values to meet contrast ratios:",
            "  • Normal text (<18pt): minimum 4.5:1 contrast ratio",
            "  • Large text (≥18pt or ≥14pt bold): minimum 3:1 contrast ratio",
            f"  • Current colors: foreground='{fg_color or 'unknown'}', background='{bg_color or 'unknown'}'",
            "Use a contrast checker tool (e.g., WebAIM Contrast Checker)",
            "Consider using darker text on light backgrounds or lighter text on dark backgrounds"
        ]
        
        css_fix = f"""/* Update these CSS rules to meet WCAG AA contrast requirements */
.text-element {{
    color: #000000;  /* Adjust foreground color */
    background-color: #FFFFFF;  /* Adjust background color */
}}

/* Or update the parent container's colors */
.container {{
    color: #333333;  /* Darker text on light background */
    background-color: #F5F5F5;
}}"""
        
        return {
            'before': html,
            'after': html,  # HTML stays same, CSS changes needed
            'css_fix': css_fix,
            'explanation': explanation,
            'steps': steps,
            'wcag_criterion': '1.4.3 Contrast (Minimum) (Level AA)',
            'impact': violation.get('impact', 'serious')
        }
    
    def _fix_aria_required_attr(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix missing required ARIA attributes."""
        # Extract role
        role_match = re.search(r'role=["\']([^"\']+)["\']', html)
        role = role_match.group(1) if role_match else 'unknown'
        
        # Common required attributes per role
        required_attrs = {
            'checkbox': ['aria-checked'],
            'radio': ['aria-checked'],
            'combobox': ['aria-expanded', 'aria-controls'],
            'slider': ['aria-valuenow', 'aria-valuemin', 'aria-valuemax'],
            'scrollbar': ['aria-valuenow', 'aria-valuemin', 'aria-valuemax'],
            'tab': ['aria-selected'],
            'tabpanel': ['aria-labelledby']
        }
        
        attrs_needed = required_attrs.get(role, ['aria-label'])
        
        # Add missing attributes
        fixed = html
        for attr in attrs_needed:
            if attr not in html:
                attr_value = 'false' if 'checked' in attr or 'expanded' in attr or 'selected' in attr else '0' if 'value' in attr else '[Provide value]'
                fixed = re.sub(
                    r'(<[^>]+)(role=)',
                    f'\\1{attr}="{attr_value}" \\2',
                    fixed,
                    count=1
                )
        
        return {
            'before': html,
            'after': fixed,
            'explanation': f"Elements with role='{role}' require specific ARIA attributes",
            'steps': [
                f"Add required attributes: {', '.join(attrs_needed)}",
                "Set appropriate values based on current state",
                "Update values dynamically with JavaScript when state changes"
            ],
            'wcag_criterion': '4.1.2 Name, Role, Value (Level A)',
            'impact': violation.get('impact', 'serious')
        }
    
    def _fix_aria_valid_attr(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix invalid ARIA attribute names (not recognized by ARIA spec)."""
        # Valid ARIA attributes as of ARIA 1.2
        valid_aria_attrs = {
            'aria-activedescendant', 'aria-atomic', 'aria-autocomplete', 'aria-busy',
            'aria-checked', 'aria-colcount', 'aria-colindex', 'aria-colspan',
            'aria-controls', 'aria-current', 'aria-describedby', 'aria-details',
            'aria-disabled', 'aria-dropeffect', 'aria-errormessage', 'aria-expanded',
            'aria-flowto', 'aria-grabbed', 'aria-haspopup', 'aria-hidden',
            'aria-invalid', 'aria-keyshortcuts', 'aria-label', 'aria-labelledby',
            'aria-level', 'aria-live', 'aria-modal', 'aria-multiline',
            'aria-multiselectable', 'aria-orientation', 'aria-owns', 'aria-placeholder',
            'aria-posinset', 'aria-pressed', 'aria-readonly', 'aria-relevant',
            'aria-required', 'aria-roledescription', 'aria-rowcount', 'aria-rowindex',
            'aria-rowspan', 'aria-selected', 'aria-setsize', 'aria-sort',
            'aria-valuemax', 'aria-valuemin', 'aria-valuenow', 'aria-valuetext'
        }
        
        # Common misspellings/invalid attributes and their corrections
        common_invalid_mappings = {
            'aria-description': None,  # Not valid, use aria-describedby instead
            'aria-descriptionby': 'aria-describedby',
            'aria-labelled-by': 'aria-labelledby',
            'aria-labeled-by': 'aria-labelledby',
            'aria-labeledby': 'aria-labelledby',
            'aria-describe': None,
            'aria-role': None,  # Use role attribute, not aria-role
        }
        
        # Find all aria attributes in the HTML
        aria_pattern = re.compile(r'\s(aria-[a-z-]+)=["\']([^"\']*)["\']', re.IGNORECASE)
        matches = aria_pattern.findall(html)
        
        fixed = html
        removed_attrs = []
        replaced_attrs = []
        
        for attr_name, attr_value in matches:
            attr_lower = attr_name.lower()
            
            # Check if it's a known invalid attribute with a mapping
            if attr_lower in common_invalid_mappings:
                replacement = common_invalid_mappings[attr_lower]
                if replacement:
                    # Replace with correct attribute
                    fixed = re.sub(
                        rf'\s{re.escape(attr_name)}=["\'][^"\']*["\']',
                        f' {replacement}="{attr_value}"',
                        fixed,
                        count=1
                    )
                    replaced_attrs.append(f'{attr_name} → {replacement}')
                else:
                    # Remove invalid attribute (no valid replacement)
                    fixed = re.sub(
                        rf'\s{re.escape(attr_name)}=["\'][^"\']*["\']',
                        '',
                        fixed,
                        count=1
                    )
                    removed_attrs.append(attr_name)
            elif attr_lower not in valid_aria_attrs:
                # Unknown/invalid attribute - remove it
                fixed = re.sub(
                    rf'\s{re.escape(attr_name)}=["\'][^"\']*["\']',
                    '',
                    fixed,
                    count=1
                )
                removed_attrs.append(attr_name)
        
        # Clean up extra spaces
        fixed = re.sub(r'\s+', ' ', fixed)
        fixed = re.sub(r'\s+>', '>', fixed)
        
        explanation_parts = []
        steps = ["Identified invalid ARIA attribute names:"]
        
        if removed_attrs:
            explanation_parts.append(f"Removed invalid attributes: {', '.join(removed_attrs)}")
            steps.append(f"  • Removed: {', '.join(removed_attrs)}")
            if 'aria-description' in removed_attrs:
                steps.append("  • Note: aria-description is not valid. Use aria-describedby with an ID reference instead.")
        
        if replaced_attrs:
            explanation_parts.append(f"Corrected misspelled attributes: {', '.join(replaced_attrs)}")
            steps.append(f"  • Corrected: {', '.join(replaced_attrs)}")
        
        if not removed_attrs and not replaced_attrs:
            explanation_parts.append("No invalid ARIA attributes found")
            steps.append("  • All ARIA attributes are valid")
        
        steps.append("Verify against ARIA 1.2 spec: https://www.w3.org/TR/wai-aria-1.2/")
        
        return {
            'before': html,
            'after': fixed,
            'explanation': '; '.join(explanation_parts),
            'steps': steps,
            'wcag_criterion': '4.1.2 Name, Role, Value (Level A)',
            'impact': violation.get('impact', 'serious')
        }
    
    def _fix_heading_order(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix heading level skipping."""
        # Extract current heading level
        heading_match = re.search(r'<h([1-6])', html, re.IGNORECASE)
        current_level = int(heading_match.group(1)) if heading_match else 0
        
        # Suggest one level lower
        suggested_level = max(1, current_level - 1)
        
        fixed = re.sub(
            r'<h[1-6]',
            f'<h{suggested_level}',
            html,
            count=1,
            flags=re.IGNORECASE
        )
        fixed = re.sub(
            r'</h[1-6]>',
            f'</h{suggested_level}>',
            fixed,
            count=1,
            flags=re.IGNORECASE
        )
        
        return {
            'before': html,
            'after': fixed,
            'explanation': "Heading levels should increase by one at a time (don't skip levels)",
            'steps': [
                f"Change <h{current_level}> to <h{suggested_level}>",
                "Ensure heading hierarchy: h1 → h2 → h3 (never h1 → h3)",
                "Use CSS to adjust visual size if needed",
                "Page should have only one <h1> (usually the main page title)"
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)',
            'impact': violation.get('impact', 'moderate')
        }
    
    def _fix_listitem(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix list item not contained in list."""
        # Wrap in <ul> tags
        fixed = f'<ul>\n  {html}\n</ul>'
        
        return {
            'before': html,
            'after': fixed,
            'explanation': "<li> elements must be direct children of <ul>, <ol>, or <menu> elements",
            'steps': [
                "Wrap <li> elements inside a <ul> (unordered) or <ol> (ordered) list",
                "Ensure all sibling list items are inside the same list container",
                "Don't use <li> for layout purposes - use <div> instead"
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)',
            'impact': violation.get('impact', 'serious')
        }
    
    def _fix_region(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix content not in landmark region."""
        # Wrap in <main> or <section> with aria-label
        fixed = f'<main>\n  {html}\n</main>'
        
        return {
            'before': html,
            'after': fixed,
            'explanation': "All page content should be contained within landmark regions for navigation",
            'steps': [
                "Wrap main content in <main> element (use only once per page)",
                "Use <nav> for navigation sections",
                "Use <aside> for complementary content",
                "Use <section aria-label='...'> for other major content regions",
                "Use <header> and <footer> for page header/footer"
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)',
            'impact': violation.get('impact', 'moderate')
        }
    
    def _fix_landmark_one_main(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix missing main landmark."""
        return {
            'before': html,
            'after': '<html lang="en">\n<head>...</head>\n<body>\n  <main>\n    <!-- Your main content goes here -->\n  </main>\n</body>\n</html>',
            'explanation': "Every page should have exactly one <main> landmark to identify the primary content",
            'steps': [
                "Add a <main> element to your page",
                "Place all primary page content inside <main>",
                "Use only ONE <main> element per page",
                "Keep <header>, <nav>, and <footer> outside of <main> if they're site-wide",
                "The <main> landmark helps screen reader users skip to main content"
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)',
            'impact': violation.get('impact', 'moderate')
        }
    
    def _fix_landmark_banner_top_level(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix banner landmark that's not at top level."""
        # Banner landmarks must be direct children of <body>
        # Two approaches: 1) Move to top level, or 2) Remove banner role
        
        # Check if it has explicit role="banner" - if so, we can remove it
        if 'role="banner"' in html:
            fixed = html.replace('role="banner"', '')
            explanation = "Removed explicit role='banner' since the header is nested and should not act as a banner landmark"
            approach = "removed explicit banner role"
        else:
            # It's a <header> with implicit banner role when at top level
            # The fix is to move it to be a direct child of <body>
            fixed = f"""<!-- Move this header to be a direct child of <body> -->
<body>
  {html}
  <!-- Rest of your page content -->
  <main>...</main>
  <footer>...</footer>
</body>"""
            explanation = "Banner landmark (<header>) must be a direct child of <body>, not nested inside other elements"
            approach = "restructured to be top-level"
        
        return {
            'before': html,
            'after': fixed,
            'explanation': explanation,
            'steps': [
                "Option 1: Move the <header> element to be a direct child of <body>",
                "Option 2: If this header is section-specific (not site-wide), change <header> to <div> to remove implicit banner role",
                "Only the site-wide header should have the banner landmark",
                "Correct structure: <body> → <header> (banner) → <main> → <footer>",
                "Note: <header> elements automatically get role='banner' when they are direct children of <body>"
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)',
            'impact': violation.get('impact', 'moderate')
        }
    
    def _fix_landmark_contentinfo_top_level(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix contentinfo landmark that's not at top level."""
        # Contentinfo landmarks must be direct children of <body>
        # Two approaches: 1) Move to top level, or 2) Remove contentinfo role
        
        # Check if it has explicit role="contentinfo" - if so, we can remove it
        if 'role="contentinfo"' in html:
            fixed = html.replace('role="contentinfo"', '')
            explanation = "Removed explicit role='contentinfo' since the footer is nested and should not act as a contentinfo landmark"
            approach = "removed explicit contentinfo role"
        else:
            # It's a <footer> with implicit contentinfo role when at top level
            # The fix is to move it to be a direct child of <body>
            fixed = f"""<!-- Move this footer to be a direct child of <body> -->
<body>
  <header>...</header>
  <main>...</main>
  {html}
</body>"""
            explanation = "Contentinfo landmark (<footer>) must be a direct child of <body>, not nested inside other elements"
            approach = "restructured to be top-level"
        
        return {
            'before': html,
            'after': fixed,
            'explanation': explanation,
            'steps': [
                "Option 1: Move the <footer> element to be a direct child of <body>",
                "Option 2: If this footer is section-specific (not site-wide), change <footer> to <div> to remove implicit contentinfo role",
                "Only the site-wide footer should have the contentinfo landmark",
                "Correct structure: <body> → <header> → <main> → <footer> (contentinfo)",
                "Note: <footer> elements automatically get role='contentinfo' when they are direct children of <body>"
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)',
            'impact': violation.get('impact', 'moderate')
        }
    
    def _fix_landmark_no_duplicate_banner(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix duplicate banner landmarks."""
        if 'role="banner"' in html:
            fixed = html.replace('role="banner"', '')
            explanation = "Page should have only ONE banner landmark. Remove role='banner' from additional headers."
            steps = [
                "Keep only ONE <header> with banner role (site-wide header)",
                "Remove role='banner' from other <header> elements",
                "Section-specific headers should be plain <header> without banner role"
            ]
        else:
            fixed = html.replace('<header', '<div class="header"').replace('</header>', '</div>')
            explanation = "Page should have only ONE banner landmark. Convert additional <header> to <div>."
            steps = [
                "Keep only ONE top-level <header> element (site-wide header)",
                "Convert other top-level <header> to <div> with class names",
                "Section headers can stay as <header> if nested in <main> or <section>"
            ]
        
        return {
            'before': html,
            'after': fixed,
            'explanation': explanation,
            'steps': steps,
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)',
            'impact': violation.get('impact', 'moderate')
        }
    
    def _fix_landmark_no_duplicate_contentinfo(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix duplicate contentinfo landmarks."""
        if 'role="contentinfo"' in html:
            fixed = html.replace('role="contentinfo"', '')
            explanation = "Page should have only ONE contentinfo landmark. Remove role='contentinfo' from additional footers."
            steps = [
                "Keep only ONE <footer> with contentinfo role (site-wide footer)",
                "Remove role='contentinfo' from other <footer> elements",
                "Section-specific footers should be plain <footer> without contentinfo role"
            ]
        else:
            fixed = html.replace('<footer', '<div class="footer"').replace('</footer>', '</div>')
            explanation = "Page should have only ONE contentinfo landmark. Convert additional <footer> to <div>."
            steps = [
                "Keep only ONE top-level <footer> element (site-wide footer)",
                "Convert other top-level <footer> to <div> with class names",
                "Section footers can stay as <footer> if nested in <main> or <section>"
            ]
        
        return {
            'before': html,
            'after': fixed,
            'explanation': explanation,
            'steps': steps,
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)',
            'impact': violation.get('impact', 'moderate')
        }
    
    def _fix_landmark_unique(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix duplicate landmark without unique labels."""
        landmark_type = 'landmark'
        suggested_label = 'Landmark description'
        
        if '<nav' in html or 'role="navigation"' in html:
            landmark_type = 'navigation'
            suggested_label = 'Main navigation'
        elif '<aside' in html or 'role="complementary"' in html:
            landmark_type = 'complementary'
            suggested_label = 'Related content'
        elif '<main' in html or 'role="main"' in html:
            landmark_type = 'main'
            suggested_label = 'Main content'
        elif '<section' in html or 'role="region"' in html:
            landmark_type = 'region'
            suggested_label = 'Section name'
        
        if 'aria-label' not in html:
            fixed = re.sub(
                r'(<(?:nav|aside|main|section|header|footer)[^>]*)(>)',
                rf'\1 aria-label="{suggested_label}"\2',
                html,
                count=1,
                flags=re.IGNORECASE
            )
        else:
            fixed = html
        
        return {
            'before': html,
            'after': fixed,
            'explanation': f"Multiple {landmark_type} landmarks must have unique labels to be distinguishable",
            'steps': [
                f"Add unique aria-label to each {landmark_type} landmark",
                "Labels should describe purpose: e.g., 'Main navigation', 'Footer navigation'",
                "Ensure labels help users distinguish between similar landmarks",
                "Screen reader users navigate by landmarks, so clear labels are essential"
            ],
            'wcag_criterion': '2.4.1 Bypass Blocks (Level A)',
            'impact': violation.get('impact', 'moderate')
        }
    
    def _fix_duplicate_id(self, html: str, node: Dict, violation: Dict) -> Dict:
        """
        Fix duplicate ID violations by generating a unique ID.
        
        This handles:
        - duplicate-id: General duplicate IDs
        - duplicate-id-active: Duplicate IDs on interactive elements (buttons, links, inputs)
        - duplicate-id-aria: Duplicate IDs referenced by ARIA attributes
        """
        # Extract the current ID value
        id_match = re.search(r'id=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if not id_match:
            # No ID found - shouldn't happen but handle gracefully
            return {
                'before': html,
                'after': html,
                'explanation': "Element has duplicate ID but ID attribute couldn't be parsed",
                'steps': [
                    "Manually inspect the element to find the duplicate ID",
                    "Change the ID to a unique value",
                    "Update any references to this ID (aria-labelledby, aria-describedby, for attributes, etc.)"
                ],
                'wcag_criterion': '4.1.1 Parsing (Level A)',
                'impact': violation.get('impact', 'serious')
            }
        
        current_id = id_match.group(1)
        
        # Extract element type for better ID suggestion
        tag_match = re.match(r'<(\w+)', html, re.IGNORECASE)
        element_type = tag_match.group(1).lower() if tag_match else 'element'
        
        # Check if this is an ARIA-related ID (used by aria-labelledby, aria-describedby, etc.)
        is_aria_id = violation.get('id') == 'duplicate-id-aria'
        
        # Check if this is an active element (interactive: button, link, input, etc.)
        is_active = violation.get('id') == 'duplicate-id-active' or element_type in ['button', 'a', 'input', 'select', 'textarea']
        
        # Generate suggested unique ID based on context
        if is_aria_id:
            suggested_id = f"{current_id}-label-{self._generate_unique_suffix()}"
            id_purpose = "ARIA reference target"
        elif is_active:
            suggested_id = f"{current_id}-{element_type}-{self._generate_unique_suffix()}"
            id_purpose = "interactive element"
        else:
            suggested_id = f"{current_id}-{self._generate_unique_suffix()}"
            id_purpose = "element"
        
        # Replace the ID in the HTML
        fixed = re.sub(
            r'(id=["\'])([^"\']+)(["\'])',
            rf'\1{suggested_id}\3',
            html,
            count=1,
            flags=re.IGNORECASE
        )
        
        # Build context-specific explanation
        violation_type = violation.get('id', 'duplicate-id')
        if violation_type == 'duplicate-id-active':
            context_note = " This is especially critical for interactive elements as duplicate IDs can break keyboard navigation and assistive technology functionality."
        elif violation_type == 'duplicate-id-aria':
            context_note = " This is critical because ARIA attributes like aria-labelledby and aria-describedby rely on unique IDs to create proper associations."
        else:
            context_note = " This violates HTML standards and can cause unpredictable behavior."
        
        return {
            'before': html,
            'after': fixed,
            'explanation': f"Each {id_purpose} must have a unique ID attribute.{context_note}",
            'steps': [
                f"Change the duplicate ID '{current_id}' to a unique value like '{suggested_id}'",
                "Search your codebase for other elements using the same ID",
                "If the ID is referenced elsewhere (e.g., in JavaScript, CSS, or ARIA attributes), update those references",
                "Tip: Use meaningful, descriptive IDs that reflect the element's purpose",
                "Consider using a naming convention like: component-type-purpose (e.g., 'header-logo-link', 'footer-social-nav')"
            ],
            'wcag_criterion': '4.1.1 Parsing (Level A) - ID attributes must be unique',
            'impact': violation.get('impact', 'serious')
        }
    
    def _generate_unique_suffix(self) -> str:
        """Generate a simple unique suffix for IDs (incremental counter or timestamp-based)."""
        import random
        return str(random.randint(1, 9999))
    
    # ========== NEW FIX FUNCTIONS FOR 37+ MISSING RULES ==========
    
    def _fix_aria_allowed_role(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix inappropriate ARIA role for element."""
        # Remove invalid role or suggest appropriate role
        role_match = re.search(r'role="([^"]+)"', html)
        if role_match:
            fixed_html = re.sub(r'role="[^"]+"', '', html)  # Remove role
            return {
                'before': html,
                'after': fixed_html.strip(),
                'explanation': 'Remove invalid ARIA role or use a semantically appropriate HTML element instead',
                'steps': [
                    'Use native HTML elements instead of ARIA roles when possible (e.g., <button> instead of <div role="button">)',
                    'If ARIA role is necessary, ensure it matches the element type',
                    'Remove the role attribute if not needed'
                ],
                'wcag_criterion': '4.1.2 Name, Role, Value (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_aria_command_name(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix missing accessible name for ARIA command."""
        return self._add_aria_label(node, 'Command button', '4.1.2 Name, Role, Value (Level A)')
    
    def _fix_aria_dialog_name(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix missing accessible name for ARIA dialog."""
        return self._add_aria_label(node, 'Dialog', '4.1.2 Name, Role, Value (Level A)')
    
    def _fix_aria_meter_name(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix missing accessible name for ARIA meter."""
        return self._add_aria_label(node, 'Progress meter', '4.1.2 Name, Role, Value (Level A)')
    
    def _fix_aria_progressbar_name(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix missing accessible name for ARIA progressbar."""
        return self._add_aria_label(node, 'Loading progress', '4.1.2 Name, Role, Value (Level A)')
    
    def _fix_aria_tooltip_name(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix missing accessible name for ARIA tooltip."""
        return self._add_aria_label(node, 'Tooltip', '4.1.2 Name, Role, Value (Level A)')
    
    def _fix_aria_treeitem_name(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix missing accessible name for ARIA treeitem."""
        return self._add_aria_label(node, 'Tree item', '4.1.2 Name, Role, Value (Level A)')
    

    def _fix_aria_conditional_attr(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix ARIA attribute used incorrectly for role."""
        return {
            'before': html,
            'after': html + ' <!-- Review: Some ARIA attributes may not be appropriate for this role -->',
            'explanation': 'Ensure ARIA attributes are appropriate for the element role',
            'steps': [
                'Check ARIA specification for which attributes are valid for this role',
                'Remove attributes that are not allowed for this role',
                'Add any required attributes that are missing'
            ],
            'wcag_criterion': '4.1.2 Name, Role, Value (Level A)'
        }
    
    def _fix_aria_deprecated_role(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix deprecated ARIA role."""
        role_match = re.search(r'role="([^"]+)"', html)
        if role_match:
            old_role = role_match.group(1)
            # Map deprecated roles to modern ones
            role_map = {
                'directory': 'list',
                'doc-biblioentry': 'listitem'
            }
            new_role = role_map.get(old_role, 'complementary')
            fixed_html = html.replace(f'role="{old_role}"', f'role="{new_role}"')
            return {
                'before': html,
                'after': fixed_html,
                'explanation': f'Replace deprecated role "{old_role}" with modern equivalent',
                'steps': [
                    f'Change role="{old_role}" to role="{new_role}"',
                    'Update any related ARIA attributes',
                    'Test with screen readers'
                ],
                'wcag_criterion': '4.1.2 Name, Role, Value (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_aria_prohibited_attr(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix ARIA attribute used on element that prohibits it."""
        # Remove prohibited ARIA attributes
        aria_attrs = re.findall(r'aria-[a-z-]+="[^"]*"', html)
        fixed_html = html
        for attr in aria_attrs:
            fixed_html = fixed_html.replace(attr, '')
        return {
            'before': html,
            'after': fixed_html.strip(),
            'explanation': 'Remove ARIA attributes that are not allowed on this element',
            'steps': [
                'Check which ARIA attributes are prohibited for this element type',
                'Remove prohibited attributes',
                'Use semantic HTML instead when possible'
            ],
            'wcag_criterion': '4.1.2 Name, Role, Value (Level A)'
        }
    
    def _fix_aria_text(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix role="text" with focusable descendants."""
        # Remove tabindex from children or remove role="text"
        fixed_html = html.replace('role="text"', '')
        return {
            'before': html,
            'after': fixed_html,
            'explanation': 'Elements with role="text" cannot have focusable descendants',
            'steps': [
                'Remove role="text" or',
                'Remove tabindex from all descendant elements',
                'Ensure no interactive elements are inside'
            ],
            'wcag_criterion': '4.1.2 Name, Role, Value (Level A)'
        }
    
    def _fix_aria_hidden_body(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix aria-hidden on body element."""
        fixed_html = re.sub(r'aria-hidden="[^"]*"', '', html)
        return {
            'before': html,
            'after': fixed_html.strip(),
            'explanation': 'The body element must not have aria-hidden="true"',
            'steps': [
                'Remove aria-hidden from the <body> element',
                'Apply aria-hidden to specific sections instead',
                'Never hide the entire page from assistive technology'
            ],
            'wcag_criterion': '4.1.2 Name, Role, Value (Level A)'
        }
    
    def _fix_input_image_alt(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix missing alt text on image button."""
        if 'alt=' not in html:
            # Insert alt attribute before closing >
            fixed_html = html.replace('>', ' alt="Submit button">', 1) if html.endswith('>') else html + ' alt="Submit button"'
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'Image buttons must have alternate text via alt attribute',
                'steps': [
                    'Add descriptive alt text that explains the button action',
                    'Example: alt="Submit form" or alt="Search"',
                    'Do not use generic text like "button" or "image"'
                ],
                'wcag_criterion': '1.1.1 Non-text Content (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_fieldset(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix missing fieldset for radio/checkbox group."""
        fixed_html = f'<fieldset>\n  <legend>Select an option</legend>\n  {html}\n</fieldset>'
        return {
            'before': html,
            'after': fixed_html,
            'explanation': 'Group related radio buttons or checkboxes in a fieldset with legend',
            'steps': [
                'Wrap the group of radio buttons/checkboxes in <fieldset>',
                'Add <legend> as first child with descriptive group label',
                'Ensure all related inputs are inside the fieldset'
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)'
        }
    
    def _fix_label_title_only(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix form field that relies only on title attribute."""
        # Extract id if present, else add one
        id_match = re.search(r'id="([^"]+)"', html)
        input_id = id_match.group(1) if id_match else f'input-{self._generate_unique_suffix()}'
        
        if not id_match:
            html = re.sub(r'<input', f'<input id="{input_id}"', html, 1)
        
        title_match = re.search(r'title="([^"]+)"', html)
        label_text = title_match.group(1) if title_match else 'Form field'
        
        fixed_html = f'<label for="{input_id}">{label_text}</label>\n{html}'
        return {
            'before': html,
            'after': fixed_html,
            'explanation': 'Add explicit label element instead of relying on title alone',
            'steps': [
                'Create a <label> element with for attribute matching input id',
                'Move title text to label',
                'Keep title as supplementary help text if needed'
            ],
            'wcag_criterion': '3.3.2 Labels or Instructions (Level A)'
        }
    
    def _fix_label_content_name_mismatch(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix label text that doesn't match accessible name."""
        return {
            'before': html,
            'after': html + ' <!-- Ensure aria-label matches visible label text -->',
            'explanation': 'Visible label text should match or be contained in accessible name',
            'steps': [
                'If using aria-label, ensure it contains the visible label text',
                'Visible label should be the start of the accessible name',
                'Remove contradicting aria-label if not needed'
            ],
            'wcag_criterion': '2.5.3 Label in Name (Level A)'
        }
    
    def _fix_link_in_text_block(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix link that's not distinguishable from text."""
        return {
            'before': html,
            'after': html,
            'explanation': 'Links must be visually distinguishable from surrounding text',
            'css_fix': '''/* Add underline or sufficient color contrast */
a {
    text-decoration: underline;
    /* OR ensure 3:1 contrast ratio between link and text */
}

/* Show underline on hover/focus */
a:hover, a:focus {
    text-decoration: underline;
}''',
            'steps': [
                'Add text-decoration: underline to links',
                'OR ensure 3:1 color contrast ratio between link and surrounding text',
                'AND ensure 4.5:1 contrast ratio for both link and text against background'
            ],
            'wcag_criterion': '1.4.1 Use of Color (Level A)'
        }
    
    def _fix_identical_links_same_purpose(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix identical link text pointing to different destinations."""
        href_match = re.search(r'href="([^"]+)"', html)
        link_dest = href_match.group(1) if href_match else 'page'
        
        # Add context to link text
        link_text_match = re.search(r'>([^<]+)<', html)
        if link_text_match:
            old_text = link_text_match.group(1)
            new_text = f'{old_text} ({link_dest.split("/")[-1]})'
            fixed_html = html.replace(f'>{old_text}<', f'>{new_text}<')
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'Add context to distinguish identical link text',
                'steps': [
                    'Make link text more specific and unique',
                    'Add context (e.g., "Read more about Product A" vs "Read more about Product B")',
                    'Use aria-label if visual text must remain the same'
                ],
                'wcag_criterion': '2.4.4 Link Purpose (In Context) (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_color_contrast_enhanced(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix enhanced color contrast (AAA)."""
        # Similar to regular contrast but with higher ratios
        return {
            'before': node.get('html', ''),
            'after': node.get('html', ''),
            'explanation': 'Text must have enhanced contrast ratio (7:1 for normal text, 4.5:1 for large text)',
            'css_fix': '''/* Increase contrast to meet AAA standards */
.text {
    color: #000000; /* Dark text on light background */
    background-color: #ffffff;
    /* OR */
    color: #ffffff; /* Light text on dark background */
    background-color: #000000;
}

/* For large text (18pt+ or 14pt+ bold), 4.5:1 is acceptable */
.large-text {
    font-size: 18pt; /* or font-size: 14pt; font-weight: bold; */
    color: #333333;
    background-color: #ffffff;
}''',
            'steps': [
                'Check current contrast ratio using a color contrast analyzer',
                'Darken text or lighten background (or vice versa) to achieve 7:1 ratio',
                'For large text (18pt+ or 14pt+ bold), 4.5:1 is acceptable'
            ],
            'wcag_criterion': '1.4.6 Contrast (Enhanced) (Level AAA)'
        }
    
    def _fix_p_as_heading(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix paragraph styled as heading."""
        # Suggest converting to proper heading
        fixed_html = html.replace('<p', '<h2', 1).replace('</p>', '</h2>', 1)
        return {
            'before': html,
            'after': fixed_html,
            'explanation': 'Use proper heading elements instead of styled paragraphs',
            'steps': [
                'Replace <p> with appropriate heading level (h1-h6)',
                'Choose heading level based on document outline',
                'Remove CSS that makes paragraph look like heading'
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)'
        }
    
    def _fix_page_has_heading_one(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix missing h1 on page."""
        return {
            'before': '<body>\n  <div class="content">Page content...</div>\n</body>',
            'after': '<body>\n  <h1>Page Title</h1>\n  <div class="content">Page content...</div>\n</body>',
            'explanation': 'Add a level-one heading (h1) as the main page title',
            'steps': [
                'Add an <h1> element near the top of the page',
                'Use the page title or main content heading',
                'Ensure only one h1 per page',
                'Place it before other content'
            ],
            'wcag_criterion': '2.4.6 Headings and Labels (Level AA)'
        }
    
    def _fix_td_has_header(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix data cell without header."""
        return {
            'before': html,
            'after': html + ' <!-- Ensure this cell has corresponding <th> in row/column -->',
            'explanation': 'Data cells must be associated with table headers',
            'steps': [
                'Add <th> elements in first row for column headers',
                'Add <th> elements in first column for row headers',
                'Use scope attribute on <th> (scope="col" or scope="row")',
                'For complex tables, use headers attribute on <td>'
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)'
        }
    
    def _fix_th_has_scope(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix table header without scope attribute."""
        if 'scope=' not in html:
            # Add scope attribute
            fixed_html = html.replace('<th', '<th scope="col"', 1) if html.startswith('<th') else html
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'Table headers must have scope attribute',
                'steps': [
                    'Add scope="col" for column headers',
                    'Add scope="row" for row headers',
                    'Use scope="colgroup" or scope="rowgroup" for header groups'
                ],
                'wcag_criterion': '1.3.1 Info and Relationships (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_scope_attr_valid(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix invalid scope attribute value."""
        # Valid values: col, row, colgroup, rowgroup
        scope_match = re.search(r'scope="([^"]+)"', html)
        if scope_match:
            current_scope = scope_match.group(1)
            if current_scope not in ['col', 'row', 'colgroup', 'rowgroup']:
                fixed_html = html.replace(f'scope="{current_scope}"', 'scope="col"')
                return {
                    'before': html,
                    'after': fixed_html,
                    'explanation': 'scope attribute must be one of: col, row, colgroup, rowgroup',
                    'steps': [
                        'Change scope to "col" for column headers',
                        'Change scope to "row" for row headers',
                        'Use "colgroup" or "rowgroup" for grouped headers'
                    ],
                    'wcag_criterion': '1.3.1 Info and Relationships (Level A)'
                }
        return self._generate_generic_fix(violation, node)
    
    def _fix_table_fake_caption(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix table using paragraph as caption."""
        return {
            'before': '<p>Table caption text</p>\n<table>...</table>',
            'after': '<table>\n  <caption>Table caption text</caption>\n  ...</table>',
            'explanation': 'Use <caption> element inside <table> for table captions',
            'steps': [
                'Move caption text inside <table> as first child',
                'Wrap caption text in <caption> element',
                'Remove the separate paragraph'
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)'
        }
    
    def _fix_layout_table(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix layout table using data table elements."""
        # Remove semantic table elements from layout table
        fixed_html = html.replace('<caption>', '<!-- <caption>').replace('</caption>', '</caption> -->')
        fixed_html = fixed_html.replace(' scope=', ' role="presentation" ')
        return {
            'before': html,
            'after': fixed_html,
            'explanation': 'Layout tables must not use <caption>, <th>, or summary attributes',
            'steps': [
                'Add role="presentation" to the table',
                'Remove <caption>, <th>, summary attributes',
                'Consider using CSS Grid or Flexbox instead of tables for layout'
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)'
        }
    
    def _fix_caption_faked(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix table caption outside table element."""
        return self._fix_table_fake_caption(violation, node)
    
    def _fix_empty_table_header(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix empty table header."""
        if '<th' in html and ('></th>' in html or 'th></th>' in html):
            fixed_html = html.replace('></th>', '>Column Header</th>')
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'Table headers must have text content',
                'steps': [
                    'Add descriptive text to <th> elements',
                    'Use abbr attribute for abbreviated header text if needed',
                    'Never leave <th> elements empty'
                ],
                'wcag_criterion': '1.3.1 Info and Relationships (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_list(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix list with invalid children."""
        return {
            'before': html,
            'after': html + ' <!-- Only <li>, <script>, or <template> allowed as direct children -->',
            'explanation': 'Lists must only contain li elements as direct children',
            'steps': [
                'Remove or wrap non-<li> content in <li> elements',
                'Move <div> or other wrappers outside the list',
                'Only <li>, <script>, and <template> are valid direct children'
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)'
        }
    
    def _fix_iframe_title(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix iframe without title."""
        if 'title=' not in html:
            src_match = re.search(r'src="([^"]+)"', html)
            if src_match:
                src_url = src_match.group(1)
                # Safely extract domain or use filename
                parts = src_url.split("/")
                if len(parts) > 2 and parts[2]:
                    title_text = f'Embedded content from {parts[2]}'
                else:
                    title_text = 'Embedded content'
            else:
                title_text = 'Embedded iframe content'
            
            fixed_html = html.replace('<iframe', f'<iframe title="{title_text}"', 1)
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'iframe elements must have a title attribute',
                'steps': [
                    'Add title attribute describing iframe content',
                    'Make title descriptive and unique',
                    'Example: title="YouTube video about accessibility"'
                ],
                'wcag_criterion': '2.4.1 Bypass Blocks (Level A) / 4.1.2 Name, Role, Value (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_area_alt(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix area element without alt text."""
        if 'alt=' not in html:
            fixed_html = html.replace('>', ' alt="Clickable area">', 1)
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'Area elements in image maps must have alt text',
                'steps': [
                    'Add alt attribute describing the linked area',
                    'Be specific about where the link goes',
                    'Example: alt="Navigate to contact page"'
                ],
                'wcag_criterion': '1.1.1 Non-text Content (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_blink(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix deprecated blink element."""
        # Remove blink tags
        fixed_html = html.replace('<blink>', '').replace('</blink>', '')
        return {
            'before': html,
            'after': fixed_html,
            'explanation': 'blink elements are deprecated and cause accessibility issues',
            'steps': [
                'Remove <blink> tags',
                'Use CSS for visual emphasis if needed (but avoid blinking)',
                'Consider using aria-live for dynamic content updates'
            ],
            'wcag_criterion': '2.2.2 Pause, Stop, Hide (Level A)'
        }
    
    def _fix_marquee(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix deprecated marquee element."""
        # Remove marquee tags
        content_match = re.search(r'<marquee[^>]*>(.*?)</marquee>', html, re.DOTALL)
        if content_match:
            content = content_match.group(1)
            fixed_html = f'<div>{content}</div>'
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'marquee elements are deprecated and cause accessibility issues',
                'steps': [
                    'Remove <marquee> tags',
                    'Use static content or CSS animations if needed',
                    'Ensure users can pause any animations'
                ],
                'wcag_criterion': '2.2.2 Pause, Stop, Hide (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_server_side_image_map(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix server-side image map."""
        fixed_html = html.replace(' ismap', '').replace(' ismap="ismap"', '')
        return {
            'before': html,
            'after': fixed_html,
            'explanation': 'Server-side image maps (ismap) should not be used',
            'steps': [
                'Remove ismap attribute',
                'Convert to client-side image map using <map> and <area>',
                'Or provide equivalent text links'
            ],
            'wcag_criterion': '2.1.1 Keyboard (Level A)'
        }
    
    def _fix_skip_link(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix skip link that's not focusable."""
        # Ensure skip link is keyboard accessible
        return {
            'before': html,
            'after': html,
            'explanation': 'Skip links must be keyboard focusable',
            'css_fix': '''/* Make skip link visible on focus */
.skip-link {
    position: absolute;
    left: -9999px;
    z-index: 999;
}

.skip-link:focus {
    left: 50%;
    top: 0;
    transform: translateX(-50%);
    background: #000;
    color: #fff;
    padding: 10px;
}''',
            'steps': [
                'Ensure skip link has valid href (e.g., href="#main-content")',
                'Make it visible when focused',
                'Test with keyboard Tab key',
                'Place skip link as first focusable element on page'
            ],
            'wcag_criterion': '2.4.1 Bypass Blocks (Level A)'
        }
    
    def _fix_hidden_content(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix hidden content that's focusable."""
        # Add tabindex="-1" or aria-hidden="true"
        if 'tabindex=' not in html:
            fixed_html = html.replace('>', ' tabindex="-1">', 1)
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'Hidden content should not be keyboard focusable',
                'steps': [
                    'Add tabindex="-1" to prevent keyboard focus',
                    'Or add aria-hidden="true" to hide from screen readers',
                    'Ensure display:none or visibility:hidden is applied'
                ],
                'wcag_criterion': '2.4.3 Focus Order (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_accesskeys(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix duplicate accesskey values."""
        key_match = re.search(r'accesskey="([^"]+)"', html)
        if key_match:
            old_key = key_match.group(1)
            new_key = chr(ord(old_key[0]) + 1) if len(old_key) > 0 else 'a'
            fixed_html = html.replace(f'accesskey="{old_key}"', f'accesskey="{new_key}"')
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'accesskey values must be unique on the page',
                'steps': [
                    'Ensure each accesskey is used only once',
                    'Consider removing accesskey (they often conflict with browser/AT shortcuts)',
                    'Document accesskeys if used'
                ],
                'wcag_criterion': '2.4.1 Bypass Blocks (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_focus_order_semantics(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix element with inappropriate tabindex."""
        return {
            'before': html,
            'after': html + ' <!-- Use native interactive elements instead of tabindex on non-interactive elements -->',
            'explanation': 'Focusable elements must have appropriate semantics',
            'steps': [
                'Use native interactive elements (<button>, <a>, <input>) when possible',
                'Add appropriate ARIA role if using tabindex on generic elements',
                'Ensure element also responds to keyboard events'
            ],
            'wcag_criterion': '4.1.2 Name, Role, Value (Level A)'
        }
    
    def _fix_focusable_no_name(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix focusable element without accessible name."""
        return self._add_aria_label(node, 'Interactive element', '4.1.2 Name, Role, Value (Level A)')
    
    def _fix_focusable_disabled(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix disabled element that's still focusable."""
        # Add tabindex="-1" to disabled elements
        if 'tabindex=' not in html:
            fixed_html = html.replace('disabled', 'disabled tabindex="-1"')
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'Disabled elements should not be focusable',
                'steps': [
                    'Add tabindex="-1" to disabled elements',
                    'Ensure CSS does not override pointer-events',
                    'Remove from tab order completely'
                ],
                'wcag_criterion': '2.4.3 Focus Order (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_meta_viewport_large(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix viewport meta that prevents zooming."""
        # Remove user-scalable=no and maximum-scale restrictions
        fixed_html = re.sub(r'user-scalable\s*=\s*no', 'user-scalable=yes', html, flags=re.IGNORECASE)
        fixed_html = re.sub(r'maximum-scale\s*=\s*[\d.]+', 'maximum-scale=5.0', fixed_html, flags=re.IGNORECASE)
        return {
            'before': html,
            'after': fixed_html,
            'explanation': 'Viewport must allow user zooming',
            'steps': [
                'Remove user-scalable=no',
                'Set maximum-scale to at least 5.0 or remove it',
                'Allow minimum-scale of 1.0'
            ],
            'wcag_criterion': '1.4.4 Resize text (Level AA)'
        }
    
    def _fix_nested_interactive(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix nested interactive controls."""
        return {
            'before': html,
            'after': html + ' <!-- Restructure: Interactive elements cannot be nested -->',
            'explanation': 'Interactive controls (buttons, links) cannot be nested inside each other',
            'steps': [
                'Remove nested interactive elements',
                'Restructure HTML to place controls as siblings',
                'Use CSS positioning if visual nesting is needed'
            ],
            'wcag_criterion': '4.1.2 Name, Role, Value (Level A)'
        }
    
    def _fix_no_autoplay_audio(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix audio/video that autoplays."""
        # Remove autoplay attribute
        fixed_html = html.replace(' autoplay', '').replace(' autoplay="autoplay"', '')
        return {
            'before': html,
            'after': fixed_html,
            'explanation': 'Audio and video must not autoplay for more than 3 seconds',
            'steps': [
                'Remove autoplay attribute',
                'Provide user control to start playback',
                'If autoplay is required, add muted attribute and provide unmute control'
            ],
            'wcag_criterion': '1.4.2 Audio Control (Level A)'
        }
    
    def _fix_css_orientation_lock(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix CSS that locks orientation."""
        return {
            'before': node.get('html', ''),
            'after': node.get('html', ''),
            'explanation': 'Content must be usable in both portrait and landscape orientations',
            'css_fix': '''/* Remove orientation locks */
@media screen and (orientation: landscape) {
    /* Allow content to adapt, don't force orientation */
}

@media screen and (orientation: portrait) {
    /* Allow content to adapt, don't force orientation */
}

/* Use responsive design instead of locking orientation */''',
            'steps': [
                'Remove transform rotations that force orientation',
                'Remove @media queries that restrict orientation',
                'Use responsive design to adapt to both orientations'
            ],
            'wcag_criterion': '1.3.4 Orientation (Level AA)'
        }
    
    def _fix_avoid_inline_spacing(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix inline styles that prevent text spacing adjustment."""
        # Remove problematic inline spacing styles
        style_attrs = ['line-height', 'letter-spacing', 'word-spacing']
        fixed_html = html
        for attr in style_attrs:
            fixed_html = re.sub(rf'{attr}:\s*[^;]+;?', '', fixed_html, flags=re.IGNORECASE)
        return {
            'before': html,
            'after': fixed_html,
            'explanation': 'Avoid setting text spacing in inline styles - use external CSS',
            'steps': [
                'Move spacing styles to external CSS',
                'Allow users to override with custom stylesheets',
                'Ensure text spacing can be adjusted to: line-height 1.5, letter-spacing 0.12em, word-spacing 0.16em'
            ],
            'wcag_criterion': '1.4.12 Text Spacing (Level AA)'
        }
    
    def _fix_frame_tested(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix frame that needs accessibility testing."""
        return {
            'before': html,
            'after': html + ' <!-- Ensure iframe content is also tested for accessibility -->',
            'explanation': 'Content within frames must also meet accessibility requirements',
            'steps': [
                'Test the content within the iframe separately',
                'Ensure iframe has descriptive title',
                'Verify iframe content is keyboard accessible',
                'Check that iframe content has proper headings and landmarks'
            ],
            'wcag_criterion': '4.1.2 Name, Role, Value (Level A)'
        }
    
    def _fix_presentation_role_conflict(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix element with presentation role that has semantic children."""
        # Remove role="presentation" or role="none"
        fixed_html = html.replace('role="presentation"', '').replace('role="none"', '')
        return {
            'before': html,
            'after': fixed_html.strip(),
            'explanation': 'Elements with role="presentation" or role="none" cannot have semantic children',
            'steps': [
                'Remove role="presentation" from parent element',
                'Or remove semantic meaning from children',
                'Or restructure HTML to avoid conflict'
            ],
            'wcag_criterion': '4.1.2 Name, Role, Value (Level A)'
        }
    
    def _fix_target_size(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix touch target that's too small."""
        return {
            'before': node.get('html', ''),
            'after': node.get('html', ''),
            'explanation': 'Touch targets must be at least 44×44 CSS pixels',
            'css_fix': '''/* Increase touch target size */
button, a, input[type="checkbox"], input[type="radio"] {
    min-width: 44px;
    min-height: 44px;
    /* Add padding if needed */
    padding: 12px 16px;
}

/* For smaller visual elements, increase clickable area with padding */
.small-icon {
    padding: 12px; /* Creates larger hit area */
}''',
            'steps': [
                'Ensure buttons and links are at least 44×44 CSS pixels',
                'Add padding to increase clickable area',
                'Test on touch devices',
                'Maintain spacing between adjacent targets'
            ],
            'wcag_criterion': '2.5.5 Target Size (Level AAA)'
        }
    
    # ========== MISSING FUNCTIONS FROM ORIGINAL 53 PATTERNS ==========
    
    def _fix_aria_allowed_attr(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix ARIA attributes not allowed on element."""
        return {
            'before': html,
            'after': html + ' <!-- Remove ARIA attributes not allowed for this role -->',
            'explanation': 'Some ARIA attributes are not appropriate for this element type or role',
            'steps': [
                'Check ARIA specification for allowed attributes',
                'Remove attributes not permitted for this element/role',
                'Use only allowed ARIA attributes'
            ],
            'wcag_criterion': '4.1.2 Name, Role, Value (Level A)'
        }
    
    def _fix_aria_hidden_focus(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix focusable element inside aria-hidden."""
        fixed_html = html.replace('tabindex="0"', 'tabindex="-1"')
        return {
            'before': html,
            'after': fixed_html,
            'explanation': 'Elements with aria-hidden="true" should not contain focusable descendants',
            'steps': [
                'Remove aria-hidden from parent or',
                'Add tabindex="-1" to focusable children or',
                'Remove focusable elements from aria-hidden container'
            ],
            'wcag_criterion': '4.1.2 Name, Role, Value (Level A)'
        }
    
    def _fix_aria_input_field_name(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix ARIA input field without accessible name."""
        return self._add_aria_label(node, 'Input field', '4.1.2 Name, Role, Value (Level A)')
    
    def _fix_aria_required_children(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix ARIA role missing required children."""
        return {
            'before': html,
            'after': html + ' <!-- Add required child roles -->',
            'explanation': 'This ARIA role requires specific child roles',
            'steps': [
                'Check ARIA spec for required child roles',
                'Add missing child elements with appropriate roles',
                'Example: role="list" requires children with role="listitem"'
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)'
        }
    
    def _fix_aria_required_parent(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix ARIA role without required parent."""
        return {
            'before': html,
            'after': html + ' <!-- Wrap in parent with required role -->',
            'explanation': 'This ARIA role must be contained in a specific parent role',
            'steps': [
                'Check ARIA spec for required parent role',
                'Wrap this element in parent with appropriate role',
                'Example: role="listitem" requires parent with role="list"'
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)'
        }
    
    def _fix_aria_roles(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix invalid ARIA role."""
        role_match = re.search(r'role="([^"]+)"', html)
        if role_match:
            invalid_role = role_match.group(1)
            fixed_html = html.replace(f'role="{invalid_role}"', '')
            return {
                'before': html,
                'after': fixed_html.strip(),
                'explanation': f'role="{invalid_role}" is not a valid ARIA role',
                'steps': [
                    'Remove the invalid role attribute',
                    'Use a valid ARIA role from the specification',
                    'Or use semantic HTML elements instead'
                ],
                'wcag_criterion': '4.1.2 Name, Role, Value (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_aria_toggle_field_name(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix ARIA toggle field without accessible name."""
        return self._add_aria_label(node, 'Toggle', '4.1.2 Name, Role, Value (Level A)')
    
    def _fix_audio_caption(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix audio without captions."""
        return {
            'before': html,
            'after': html + '\n<track kind="captions" src="captions.vtt" srclang="en" label="English">',
            'explanation': 'Audio elements must have captions or transcripts',
            'steps': [
                'Add <track> element with captions',
                'Or provide a transcript link',
                'Ensure captions are synchronized with audio'
            ],
            'wcag_criterion': '1.2.1 Audio-only and Video-only (Level A)'
        }
    
    def _fix_autocomplete_valid(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix invalid autocomplete value."""
        # Common invalid values and their corrections
        autocomplete_map = {
            'username': 'username',
            'email': 'email',
            'phone': 'tel',
            'address': 'street-address'
        }
        fixed_html = html
        for invalid, valid in autocomplete_map.items():
            if f'autocomplete="{invalid}"' in html:
                fixed_html = html.replace(f'autocomplete="{invalid}"', f'autocomplete="{valid}"')
                break
        return {
            'before': html,
            'after': fixed_html,
            'explanation': 'autocomplete attribute must use valid values from HTML spec',
            'steps': [
                'Check HTML autocomplete specification for valid values',
                'Use standard values like: name, email, tel, street-address, etc.',
                'Remove autocomplete if not needed'
            ],
            'wcag_criterion': '1.3.5 Identify Input Purpose (Level AA)'
        }
    
    def _fix_bypass(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix missing skip navigation mechanism."""
        return {
            'before': '<body>\n  <header>...</header>\n  <main>...</main>',
            'after': '<body>\n  <a href="#main-content" class="skip-link">Skip to main content</a>\n  <header>...</header>\n  <main id="main-content">...</main>',
            'explanation': 'Add a skip link to bypass repetitive content',
            'steps': [
                'Add a skip link as first element in <body>',
                'Link to main content area using id',
                'Make skip link visible on focus'
            ],
            'wcag_criterion': '2.4.1 Bypass Blocks (Level A)'
        }
    
    def _fix_definition_list(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix definition list structure."""
        return {
            'before': html,
            'after': '<dl>\n  <dt>Term</dt>\n  <dd>Definition</dd>\n</dl>',
            'explanation': 'Definition lists must only contain dt and dd elements',
            'steps': [
                'Ensure only <dt> and <dd> are direct children of <dl>',
                'Remove or wrap other content',
                'Alternate between <dt> and <dd> elements'
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)'
        }
    
    def _fix_dlitem(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix dt/dd outside definition list."""
        fixed_html = f'<dl>\n  {html}\n</dl>'
        return {
            'before': html,
            'after': fixed_html,
            'explanation': 'dt and dd elements must be contained within dl',
            'steps': [
                'Wrap <dt> and <dd> elements in a <dl>',
                'Ensure proper pairing of terms and definitions',
                'Do not use dt/dd outside of definition lists'
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)'
        }
    
    def _fix_document_title(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix missing document title."""
        return {
            'before': '<head>\n  <meta charset="UTF-8">\n</head>',
            'after': '<head>\n  <meta charset="UTF-8">\n  <title>Page Title</title>\n</head>',
            'explanation': 'Every HTML document must have a descriptive title',
            'steps': [
                'Add <title> element in <head>',
                'Make title descriptive and unique for each page',
                'Keep title concise (50-60 characters)'
            ],
            'wcag_criterion': '2.4.2 Page Titled (Level A)'
        }
    
    def _fix_empty_heading(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix empty heading."""
        level_match = re.search(r'<h([1-6])', html)
        if level_match:
            level = level_match.group(1)
            fixed_html = html.replace(f'></h{level}>', f'>Heading Text</h{level}>')
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'Headings must not be empty',
                'steps': [
                    'Add descriptive text to the heading',
                    'Or remove the heading if not needed',
                    'Never leave headings empty'
                ],
                'wcag_criterion': '2.4.6 Headings and Labels (Level AA)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_form_field_multiple_labels(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix form field with multiple labels."""
        return {
            'before': html,
            'after': html + ' <!-- Remove extra label elements -->',
            'explanation': 'Form fields should have only one label element',
            'steps': [
                'Keep one <label> element per form field',
                'Remove duplicate labels',
                'Use aria-describedby for additional help text'
            ],
            'wcag_criterion': '3.3.2 Labels or Instructions (Level A)'
        }
    
    def _fix_frame_title(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix frame without title."""
        if 'title=' not in html:
            fixed_html = html.replace('<frame', '<frame title="Frame content"', 1)
            fixed_html = fixed_html.replace('<iframe', '<iframe title="Embedded content"', 1)
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'Frames must have a title attribute',
                'steps': [
                    'Add title attribute to frame/iframe',
                    'Make title descriptive',
                    'Describe the frame content purpose'
                ],
                'wcag_criterion': '2.4.1 Bypass Blocks (Level A) / 4.1.2 Name, Role, Value (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_html_has_lang(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix missing lang attribute on html."""
        fixed_html = html.replace('<html', '<html lang="en"', 1)
        return {
            'before': html,
            'after': fixed_html,
            'explanation': 'HTML element must have a lang attribute',
            'steps': [
                'Add lang attribute to <html> element',
                'Use appropriate language code (e.g., "en" for English)',
                'Ensure lang matches page content language'
            ],
            'wcag_criterion': '3.1.1 Language of Page (Level A)'
        }
    
    def _fix_html_lang_valid(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix invalid lang attribute value."""
        lang_match = re.search(r'lang="([^"]+)"', html)
        if lang_match:
            invalid_lang = lang_match.group(1)
            fixed_html = html.replace(f'lang="{invalid_lang}"', 'lang="en"')
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'lang attribute must use valid language code',
                'steps': [
                    'Use ISO 639-1 language codes (e.g., en, fr, es, de)',
                    'Check https://www.w3.org/International/questions/qa-choosing-language-tags',
                    'Ensure lang code matches actual content language'
                ],
                'wcag_criterion': '3.1.1 Language of Page (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_html_xml_lang_mismatch(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix mismatch between lang and xml:lang."""
        lang_match = re.search(r'lang="([^"]+)"', html)
        if lang_match:
            lang_value = lang_match.group(1)
            fixed_html = re.sub(r'xml:lang="[^"]+"', f'xml:lang="{lang_value}"', html)
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'lang and xml:lang attributes must match',
                'steps': [
                    'Ensure both lang and xml:lang have the same value',
                    'Or remove xml:lang if not needed for XHTML',
                    'Keep both attributes synchronized'
                ],
                'wcag_criterion': '3.1.1 Language of Page (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_meta_refresh(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix meta refresh redirect."""
        return {
            'before': html,
            'after': '<!-- Remove meta refresh or set delay to 0 -->\n<!-- Use server-side redirect instead -->',
            'explanation': 'Meta refresh should not be used for timed redirects',
            'steps': [
                'Remove meta refresh tag',
                'Use server-side redirects (HTTP 301/302)',
                'Or use client-side redirect with user control',
                'If refresh needed, set delay to 0 for instant redirect'
            ],
            'wcag_criterion': '2.2.1 Timing Adjustable (Level A) / 3.2.5 Change on Request (Level AAA)'
        }
    
    def _fix_meta_viewport(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix problematic viewport meta."""
        # Remove user-scalable=no
        fixed_html = re.sub(r',?\s*user-scalable\s*=\s*no', '', html, flags=re.IGNORECASE)
        fixed_html = re.sub(r',?\s*maximum-scale\s*=\s*1\.0', '', fixed_html, flags=re.IGNORECASE)
        return {
            'before': html,
            'after': fixed_html,
            'explanation': 'Viewport must not prevent zooming',
            'steps': [
                'Remove user-scalable=no',
                'Remove maximum-scale=1.0',
                'Allow users to zoom for accessibility'
            ],
            'wcag_criterion': '1.4.4 Resize Text (Level AA)'
        }
    
    def _fix_object_alt(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix object without alt text."""
        if 'aria-label=' not in html and 'alt=' not in html:
            fixed_html = html.replace('<object', '<object aria-label="Embedded object"', 1)
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'Object elements must have accessible text',
                'steps': [
                    'Add aria-label or aria-labelledby',
                    'Or provide alt text in nested element',
                    'Describe the object content'
                ],
                'wcag_criterion': '1.1.1 Non-text Content (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_role_img_alt(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix element with role="img" without alt text."""
        if 'aria-label=' not in html:
            fixed_html = html.replace('role="img"', 'role="img" aria-label="Image description"')
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'Elements with role="img" must have accessible text',
                'steps': [
                    'Add aria-label with descriptive text',
                    'Or add aria-labelledby pointing to visible label',
                    'Describe what the image conveys'
                ],
                'wcag_criterion': '1.1.1 Non-text Content (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_scrollable_region_focusable(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix scrollable region not keyboard accessible."""
        if 'tabindex=' not in html:
            fixed_html = html.replace('>', ' tabindex="0">', 1)
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'Scrollable regions must be keyboard accessible',
                'steps': [
                    'Add tabindex="0" to make focusable',
                    'Or ensure interactive content inside is focusable',
                    'Test with keyboard navigation'
                ],
                'wcag_criterion': '2.1.1 Keyboard (Level A)',
                'impact': violation.get('impact', 'serious')
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_select_name(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix select without accessible name."""
        id_match = re.search(r'id="([^"]+)"', html)
        select_id = id_match.group(1) if id_match else f'select-{self._generate_unique_suffix()}'
        
        if not id_match:
            html = re.sub(r'<select', f'<select id="{select_id}"', html, 1)
        
        fixed_html = f'<label for="{select_id}">Select option</label>\n{html}'
        return {
            'before': html,
            'after': fixed_html,
            'explanation': 'Select elements must have accessible labels',
            'steps': [
                'Add <label> element with for attribute',
                'Or add aria-label attribute',
                'Make label descriptive of select purpose'
            ],
            'wcag_criterion': '4.1.2 Name, Role, Value (Level A)'
        }
    
    def _fix_svg_img_alt(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix SVG without accessible text."""
        if '<title>' not in html and 'aria-label=' not in html:
            fixed_html = html.replace('<svg', '<svg role="img" aria-label="SVG image description"', 1)
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'SVG images must have accessible text',
                'steps': [
                    'Add <title> element as first child of SVG',
                    'Or add aria-label to SVG element',
                    'Or add role="img" with aria-label'
                ],
                'wcag_criterion': '1.1.1 Non-text Content (Level A)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_tabindex(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix positive tabindex value."""
        tabindex_match = re.search(r'tabindex="(\d+)"', html)
        if tabindex_match:
            value = tabindex_match.group(1)
            if int(value) > 0:
                fixed_html = html.replace(f'tabindex="{value}"', 'tabindex="0"')
                return {
                    'before': html,
                    'after': fixed_html,
                    'explanation': 'tabindex values must not be greater than 0',
                    'steps': [
                        'Change positive tabindex to 0',
                        'Or remove tabindex if element is naturally focusable',
                        'Use CSS for visual order instead'
                    ],
                    'wcag_criterion': '2.4.3 Focus Order (Level A)'
                }
        return self._generate_generic_fix(violation, node)
    
    def _fix_table_duplicate_name(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix table with duplicate summary and caption."""
        return {
            'before': html,
            'after': html + ' <!-- Make caption and summary different or remove summary -->',
            'explanation': 'Table caption and summary should not be identical',
            'steps': [
                'Make caption brief and summary more detailed',
                'Or remove summary attribute (deprecated in HTML5)',
                'Use different text for caption and aria-describedby'
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)'
        }
    
    def _fix_td_headers_attr(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix td headers attribute pointing to non-existent headers."""
        return {
            'before': html,
            'after': html + ' <!-- Ensure headers attribute points to valid th id values -->',
            'explanation': 'td headers attribute must reference existing th element ids',
            'steps': [
                'Check that headers attribute values match th element ids',
                'Add missing ids to th elements',
                'Or use scope attribute on th instead'
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)'
        }
    
    def _fix_th_has_data_cells(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix th without associated data cells."""
        return {
            'before': html,
            'after': html + ' <!-- Ensure this header has corresponding td cells -->',
            'explanation': 'Table headers must have data cells they describe',
            'steps': [
                'Ensure each th has associated td cells in same row/column',
                'Remove th if no data cells',
                'Or convert to td if not a header'
            ],
            'wcag_criterion': '1.3.1 Info and Relationships (Level A)'
        }
    
    def _fix_valid_lang(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix invalid lang attribute on any element."""
        lang_match = re.search(r'lang="([^"]+)"', html)
        if lang_match:
            invalid_lang = lang_match.group(1)
            fixed_html = html.replace(f'lang="{invalid_lang}"', 'lang="en"')
            return {
                'before': html,
                'after': fixed_html,
                'explanation': 'lang attribute must use valid language code',
                'steps': [
                    'Use ISO 639-1 language codes',
                    'Common codes: en (English), es (Spanish), fr (French), de (German)',
                    'Match code to actual content language'
                ],
                'wcag_criterion': '3.1.2 Language of Parts (Level AA)'
            }
        return self._generate_generic_fix(violation, node)
    
    def _fix_video_caption(self, html: str, node: Dict, violation: Dict) -> Dict:
        """Fix video without captions."""
        return {
            'before': html,
            'after': html + '\n<track kind="captions" src="captions.vtt" srclang="en" label="English">',
            'explanation': 'Video elements must have captions',
            'steps': [
                'Add <track> element with kind="captions"',
                'Create WebVTT caption file',
                'Ensure captions are synchronized with video'
            ],
            'wcag_criterion': '1.2.2 Captions (Prerecorded) (Level A)'
        }
    
    def _generate_generic_fix(self, violation: Dict, node: Dict) -> Dict:
        """Generate a generic fix when no specific pattern exists."""
        html = node.get('html', '').strip()
        
        # Extract helpful information from violation
        description = violation.get('description', 'Accessibility violation detected')
        help_url = violation.get('helpUrl', '')
        impact = violation.get('impact', 'unknown')
        
        # Generic explanation
        explanation = description
        steps = [
            f"Review the violation details: {description}",
            f"Consult WCAG documentation: {help_url}",
            "Update the HTML element to meet accessibility requirements"
        ]
        
        return {
            'before': html,
            'after': html + ' <!-- Fix needed: See violation details -->',
            'explanation': explanation,
            'steps': steps,
            'wcag_criterion': 'See violation help URL',
            'impact': impact
        }
