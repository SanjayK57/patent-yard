"""Invention studio."""

from ..base import icon


class Studio:
    def studio(self):
        body = f"""<div class="page studiopage">
<div class="sechead"><div><h1>Invention studio</h1><p>Turn a patent, or your own idea, into a ready-made prompt and a PDF brief for Claude. Claude then works with you on modern directions, a first prior-art search, a rough provisional draft, sketches or a prototype plan. It runs in your own Claude account, and nothing you type here leaves your browser until you paste it there.</p></div></div>
<div class="intent" role="group" aria-label="How to start">
  <button class="intentcard" type="button" data-start="patent" aria-pressed="false">{icon("sheet")}<b>Start from a patent</b><span>Pick one from the yard. Its claims and drawings go into the brief, and Claude works from them.</span></button>
  <button class="intentcard" type="button" data-start="idea" aria-pressed="false">{icon("spark")}<b>Start with your own idea</b><span>Describe it in a few lines, or leave it blank and let Claude propose directions first.</span></button>
</div>
<ol class="howto stagebar" aria-label="Steps"><li data-stage="1"><b>Describe it</b></li><li data-stage="2"><b>Pick a task</b></li><li data-stage="3"><b>Open Claude</b></li></ol>
<div class="studio" id="studioWork">
  <section class="spanel" aria-labelledby="sIn"><h2 id="sIn" class="sr">Your invention</h2><div class="stack" id="studioForm">
    <div class="fgroup picker"><label for="pq">Start from a patent <span class="opt">optional</span></label><input class="field" id="pq" type="search" autocomplete="off" placeholder="Search by name or patent number"><ul id="pickList" role="listbox" hidden></ul><div id="picked"></div></div>
    <div class="fgroup"><label for="iName">Invention name <span class="opt">optional</span></label><input class="field" id="iName" maxlength="120" placeholder="Self-leveling camp stove"></div>
    <div class="fgroup"><label for="iPitch">One-line pitch <span class="opt">optional</span></label><input class="field" id="iPitch" maxlength="300" placeholder="What it does, for whom, in one sentence"></div>
    <div class="fgroup"><label for="iDesc">How it works <span class="opt">optional</span></label><textarea class="field" id="iDesc" maxlength="8000" placeholder="Parts, how they connect, how someone uses it. Rough notes are fine."></textarea></div>
    <div class="fgroup"><label for="iNew">What's new <span class="opt">optional</span></label><textarea class="field short" id="iNew" maxlength="3000" placeholder="The part nobody has done before."></textarea><small>Leave these blank to let Claude propose directions first.</small></div>
    <p class="muted draftnote">Your draft saves in this browser as you type. Nothing leaves it until you paste the prompt into Claude or save it to your bench.</p>
  </div></section>
  <section class="sout" aria-labelledby="sTask">
    <div class="block"><h2 id="sTask">Task</h2><div class="tasks" id="tasks"></div></div>
    <div class="docframe">
      <div class="docbar"><label for="prompt">Prompt for Claude</label><span class="muted" id="promptSize" aria-live="polite"></span><button class="btn quiet sm" type="button" id="copyPrompt">{icon("copy")}Copy</button></div>
      <textarea class="field prompt" id="prompt" readonly></textarea>
    </div>
    <div class="rowbtns sacts"><button class="btn primary lg" type="button" id="openClaude">{icon("spark")}Copy prompt and open Claude</button><button class="btn secondary" type="button" id="pdfBrief">{icon("file")}Download PDF brief</button></div>
    <div class="rowbtns"><button class="btn quiet sm" type="button" id="saveIdea">{icon("bookmark")}Save to my bench</button><span class="status" id="studioStatus" aria-live="polite"></span></div>
  </section>
</div></div>"""
        self.page("/studio/", "Invention studio", "Turn a free-to-use patent or your own idea into a ready-made prompt and PDF brief for Claude: modern directions, a first prior-art search and a rough provisional patent draft.",
                  body, section="/studio/", scripts=("studio",))
