"""Invention studio."""

from ..base import icon


class Studio:
    def studio(self):
        body = f"""<div class="page">
<div class="sechead"><div><h1>Invention studio</h1><p>Turn a patent, or your own idea, into a ready-made prompt and a PDF brief for Claude. Claude then works with you on modern directions, a first prior-art search, a rough provisional draft, sketches or a prototype plan. It runs in your own Claude account, and nothing you type here leaves your browser until you paste it there.</p></div></div>
<div class="howto"><div><b>Describe it.</b> Start from a patent here or from your own idea.</div><div><b>Pick a task.</b> We write the prompt and a PDF brief with the patent's claims and drawings.</div><div><b>Open Claude.</b> Paste the prompt, attach the brief, and work through it together.</div></div>
<div class="studio">
  <div class="panel"><div class="stack" id="studioForm">
    <div class="fgroup picker"><label for="pq">Start from a patent (optional)</label><input class="field" id="pq" type="search" autocomplete="off" placeholder="Search by name or patent number"><ul id="pickList" role="listbox" hidden></ul><div id="picked"></div></div>
    <p class="muted draftnote">Your draft saves in this browser as you type. Nothing leaves it until you paste the prompt into Claude or save it to your bench.</p>
<div class="fgroup"><label for="iName">Invention name <span class="opt">optional</span></label><input class="field" id="iName" maxlength="120" placeholder="Self-leveling camp stove"></div>
    <div class="fgroup"><label for="iPitch">One-line pitch <span class="opt">optional</span></label><input class="field" id="iPitch" maxlength="300" placeholder="What it does, for whom, in one sentence"></div>
    <div class="fgroup"><label for="iDesc">How it works <span class="opt">optional</span></label><textarea class="field" id="iDesc" maxlength="8000" placeholder="Parts, how they connect, how someone uses it. Rough notes are fine."></textarea></div>
    <div class="fgroup"><label for="iNew">What's new <span class="opt">optional</span></label><textarea class="field short" id="iNew" maxlength="3000" placeholder="The part nobody has done before."></textarea><small>Leave these blank to let Claude propose directions first.</small></div>
  </div></div>
  <div class="stack">
    <div class="block"><h2>Task</h2><div class="tasks" id="tasks"></div></div>
    <div class="fgroup"><label for="prompt">Prompt for Claude</label><textarea class="field prompt" id="prompt" readonly></textarea></div>
    <div class="rowbtns"><button class="btn primary" type="button" id="openClaude">{icon("spark")}Copy prompt and open Claude</button><button class="btn secondary" type="button" id="pdfBrief">{icon("file")}Download PDF brief</button><button class="btn quiet" type="button" id="copyPrompt">{icon("copy")}Copy</button></div>
    <div class="rowbtns"><button class="btn secondary sm" type="button" id="saveIdea">Save to my bench</button><span class="status" id="studioStatus" aria-live="polite"></span></div>
  </div>
</div></div>"""
        self.page("/studio/", "Invention studio", "Turn a free-to-use patent or your own idea into a ready-made prompt and PDF brief for Claude: modern directions, a first prior-art search and a rough provisional patent draft.",
                  body, section="/studio/", scripts=("studio",))
