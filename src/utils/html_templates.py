def get_preview_html_template():
    """
    Returns the HTML template for the email preview page
    """
    return """<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .draft-container {
            margin: 20px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .draft-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #eee;
        }
        .receiver-info {
            margin: 0;
            color: #333;
        }
        .button-group {
            display: flex;
            gap: 10px;
        }
        .copy-button {
            background-color: #0066cc;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        .copy-button:hover {
            background-color: #0052a3;
            transform: translateY(-1px);
        }
        .copy-button.copied {
            background-color: #4CAF50;
        }
        .subject-button {
            background-color: #4a6da7;
        }
        .email-content {
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            line-height: 1.6;
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
            text-align: center;
            padding-bottom: 20px;
            border-bottom: 2px solid #0066cc;
        }
        .template-info {
            text-align: center;
            font-style: italic;
            color: #666;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <h1>Email Drafts for {{company}}</h1>
    <div class="template-info">Using template: {{template_name}}</div>

    {{draft_containers}}

    <script>
        function copyToClipboard(button, text) {
            navigator.clipboard.writeText(text).then(function() {
                const originalText = button.textContent;
                button.textContent = 'Copied!';
                button.classList.add('copied');
                setTimeout(function() {
                    button.textContent = originalText;
                    button.classList.remove('copied');
                }, 2000);
            }).catch(function(err) {
                console.error('Failed to copy:', err);
                button.textContent = 'Failed to copy';
                setTimeout(function() {
                    button.textContent = originalText;
                }, 2000);
            });
        }
    </script>
</body>
</html>"""


def get_draft_container_template():
    """
    Returns the HTML template for an individual draft container
    """
    return """<div class="draft-container">
    <div class="draft-header">
        <h3 class="receiver-info">To: {{recruiter_name}} {{email_display}}</h3>
        <div class="button-group">
            <button class="copy-button" onclick="copyToClipboard(this, `{{draft_plain}}`)">
                Copy Text
            </button>
            <button class="copy-button subject-button" onclick="copyToClipboard(this, `{{subject}}`)">
                Copy Subject
            </button>
        </div>
    </div>
    <div class="email-content">
        {{draft_html}}
    </div>
</div>"""