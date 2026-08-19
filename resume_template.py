RESUME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page { size: A4; margin: 1.5cm 1.8cm; }
    * { box-sizing: border-box; }
    body {
        font-family: 'Helvetica', 'Arial', sans-serif;
        font-size: 10.5pt;
        color: #1a1a1a;
        line-height: 1.45;
    }
    h1 { font-size: 20pt; margin: 0 0 2px 0; color: #111; }
    .contact { font-size: 9.5pt; color: #444; margin-bottom: 12px; }
    .contact a { color: #444; text-decoration: none; }
    h2 {
        font-size: 11.5pt;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 1.5px solid #333;
        padding-bottom: 2px;
        margin: 14px 0 6px 0;
        color: #111;
    }
    .summary { margin-bottom: 4px; text-align: justify; }
    .entry { margin-bottom: 8px; }
    .entry-header { display: flex; justify-content: space-between; font-weight: bold; }
    .entry-sub { font-style: italic; color: #333; font-size: 10pt; }
    ul { margin: 4px 0 0 0; padding-left: 16px; }
    li { margin-bottom: 2px; }
    .skills-row { margin-bottom: 3px; }
    .skills-row b { display: inline-block; min-width: 130px; }
    .tag {
        display: inline-block;
        background: #f0f0f0;
        padding: 1px 6px;
        border-radius: 3px;
        margin: 1px 2px 1px 0;
        font-size: 9pt;
    }
</style>
</head>
<body>
    <h1>{{ personal_information.name }}</h1>
    <div class="contact">
        {{ personal_information.location }} |
        {{ personal_information.email }} |
        {{ personal_information.phone }}
        {% if personal_information.linkedin and personal_information.linkedin != 'null' %} | {{ personal_information.linkedin }}{% endif %}
        {% if personal_information.github and personal_information.github != 'null' %} | {{ personal_information.github }}{% endif %}
        {% if personal_information.portfolio and personal_information.portfolio != 'null' %} | {{ personal_information.portfolio }}{% endif %}
    </div>

    <h2>Professional Summary</h2>
    <p class="summary">{{ professional_summary }}</p>

    <h2>Technical Skills</h2>
    {% for category, items in technical_skills.items() %}
        {% if items %}
        <div class="skills-row"><b>{{ category.replace('_', ' ').title() }}:</b> {{ items | join(', ') }}</div>
        {% endif %}
    {% endfor %}

    <h2>Projects</h2>
    {% for p in projects %}
    <div class="entry">
        <div class="entry-header"><span>{{ p.project_name }}</span></div>
        <div class="entry-sub">{{ p.technologies | join(', ') }}{% if p.live_demo and p.live_demo != 'null' %} | {{ p.live_demo }}{% endif %}</div>
        <p>{{ p.description }}</p>
    </div>
    {% endfor %}

    <h2>Experience</h2>
    {% for e in experience %}
    <div class="entry">
        <div class="entry-header">
            <span>{{ e.job_title }}{% if e.company and e.company != 'null' %} — {{ e.company }}{% endif %}</span>
            <span>{{ e.start_date }} – {{ 'Present' if e.currently_working else e.end_date }}</span>
        </div>
        {% if e.responsibilities %}
        <ul>{% for r in e.responsibilities %}<li>{{ r }}</li>{% endfor %}</ul>
        {% endif %}
    </div>
    {% endfor %}

    <h2>Education</h2>
    {% for ed in education %}
    <div class="entry">
        <div class="entry-header">
            <span>{{ ed.degree }}{% if ed.specialization and ed.specialization != 'null' %} in {{ ed.specialization }}{% endif %}</span>
            <span>{{ ed.start_date }} – {{ ed.end_date }}</span>
        </div>
        <div class="entry-sub">{{ ed.university }}{% if ed.cgpa %} | {{ ed.cgpa }}{% endif %}</div>
    </div>
    {% endfor %}


    {% if languages %}
    <h2>Languages</h2>
    <p>{{ languages | join(', ') }}</p>
    {% endif %}
</body>
</html>
"""