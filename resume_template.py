RESUME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page { size: A4; margin: 1.6cm 1.8cm; }
    * { box-sizing: border-box; }

    /* ---- ATS-safe base: single column, no grid/table layouts, standard font ---- */
    body {
        font-family: Arial, Helvetica, sans-serif;
        font-size: 10.5pt;
        color: #1a1a1a;
        line-height: 1.45;
    }

    h1 {
        font-size: 19pt;
        font-weight: bold;
        margin: 0 0 3px 0;
        color: #111;
    }

    .contact {
        font-size: 9.5pt;
        color: #333;
        margin-bottom: 10px;
    }
    .contact span { margin-right: 10px; }
    .contact a { color: #333; text-decoration: none; }

    /* Standard, plain-text section headers -> ATS parsers recognise these easily */
    h2 {
        font-size: 11.5pt;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        border-bottom: 1px solid #333;
        padding-bottom: 2px;
        margin: 13px 0 6px 0;
        color: #111;
    }

    .summary { margin: 0 0 4px 0; text-align: left; }

    .entry { margin-bottom: 9px; }

    /* Use a simple block instead of flex/grid for header rows so text
       extracts top-to-bottom, left-to-right in the exact reading order */
    .entry-title { font-weight: bold; font-size: 10.5pt; }
    .entry-dates { font-size: 10pt; color: #333; }
    .entry-sub { font-style: italic; color: #333; font-size: 10pt; margin: 1px 0 2px 0; }

    ul { margin: 3px 0 0 0; padding-left: 16px; }
    li { margin-bottom: 2px; }

    /* Skills: plain stacked lines, NOT a CSS grid/table.
       Grids/tables can scramble word order when parsed by ATS software. */
    .skills-row {
        font-size: 10.5pt;
        line-height: 1.5;
        margin-bottom: 2px;
    }
    .skills-row b { color: #111; }
</style>
</head>
<body>

    <h1>{{ personal_information.name }}</h1>
    <div class="contact">
        <span>{{ personal_information.location }}</span>
        <span>{{ personal_information.email }}</span>
        <span>{{ personal_information.phone }}</span>
        {% if personal_information.linkedin and personal_information.linkedin != 'null' %}<span>{{ personal_information.linkedin }}</span>{% endif %}
        {% if personal_information.github and personal_information.github != 'null' %}<span>{{ personal_information.github }}</span>{% endif %}
        {% if personal_information.portfolio and personal_information.portfolio != 'null' %}<span>{{ personal_information.portfolio }}</span>{% endif %}
    </div>

    <h2>Professional Summary</h2>
    <p class="summary">{{ professional_summary }}</p>

    <h2>Technical Skills</h2>
    {% for category, items in technical_skills.items() %}
        {% if items %}
        <div class="skills-row"><b>{{ category.replace('_', ' ').title() }}:</b> {{ items | join(', ') }}</div>
        {% endif %}
    {% endfor %}

    {% if experience %}
    <h2>Experience</h2>
    {% for e in experience %}
    <div class="entry">
        <div class="entry-title">{{ e.job_title }}{% if e.company and e.company != 'null' %}, {{ e.company }}{% endif %}</div>
        <div class="entry-dates">{{ e.start_date }} - {{ 'Present' if e.currently_working else e.end_date }}</div>
        {% if e.responsibilities %}
        <ul>{% for r in e.responsibilities %}<li>{{ r }}</li>{% endfor %}</ul>
        {% endif %}
    </div>
    {% endfor %}
    {% endif %}

    {% if projects %}
    <h2>Projects</h2>
    {% for p in projects %}
    <div class="entry">
        <div class="entry-title">{{ p.project_name }}</div>
        <div class="entry-sub">{{ p.technologies | join(', ') }}{% if p.live_demo and p.live_demo != 'null' %} | {{ p.live_demo }}{% endif %}</div>
        <p style="margin: 2px 0 2px 0;">{{ p.description }}</p>
        {% if p.github and p.github != 'null' %}<p style="margin: 0;">{{ p.github }}</p>{% endif %}
    </div>
    {% endfor %}
    {% endif %}

    <h2>Education</h2>
    {% for ed in education %}
    <div class="entry">
        <div class="entry-title">{{ ed.degree }}{% if ed.specialization and ed.specialization != 'null' %} in {{ ed.specialization }}{% endif %}</div>
        <div class="entry-dates">{{ ed.start_date }} - {{ ed.end_date }}</div>
        <div class="entry-sub">{{ ed.university }}{% if ed.cgpa %} | {{ ed.cgpa }}{% endif %}</div>
    </div>
    {% endfor %}

    {% if languages %}
    <h2>Languages</h2>
    <p style="margin:0;">{{ languages | join(', ') }}</p>
    {% endif %}

</body>
</html>
"""