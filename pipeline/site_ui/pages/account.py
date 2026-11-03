"""My bench, saved patents and settings."""

from ..base import E, full_date, icon


class Account:
    def saved(self):
        body = f"""<div class="page">
<div class="sechead"><div><h1>Saved patents</h1><p>Patents you saved with the {icon("bookmark")} button. They're kept in this browser, so no account is needed.</p></div><a class="btn secondary" href="/browse/">Browse patents</a></div>
<div class="grid" id="savedGrid"></div>
<div class="empty" id="savedEmpty" hidden><b>Nothing saved yet</b><p>Tap Save on any patent, or the bookmark on a card, and it shows up here.</p></div>
</div>"""
        self.page("/saved/", "Saved patents", "Patents you saved on Patent Yard.", body, scripts=("saved",), index=False)

    def account(self):
        g = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#4285F4" d="M22.6 12.3c0-.8-.1-1.6-.2-2.3H12v4.4h5.9a5 5 0 0 1-2.2 3.3v2.7h3.6c2.1-1.9 3.3-4.8 3.3-8.1z"/><path fill="#34A853" d="M12 23c3 0 5.5-1 7.3-2.7l-3.6-2.7c-1 .7-2.2 1.1-3.7 1.1-2.9 0-5.3-1.9-6.2-4.5H2.1v2.8A11 11 0 0 0 12 23z"/><path fill="#FBBC05" d="M5.8 14.2a6.6 6.6 0 0 1 0-4.3V7.1H2.1a11 11 0 0 0 0 9.9l3.7-2.8z"/><path fill="#EA4335" d="M12 5.4c1.6 0 3.1.6 4.2 1.7l3.2-3.2A11 11 0 0 0 2.1 7.1l3.7 2.8C6.7 7.3 9.1 5.4 12 5.4z"/></svg>'
        body = f"""<div class="page">
<div id="loadView"><p class="muted loading-row"><span class="think">Loading your account…</span></p><noscript><p class="empty">Accounts need JavaScript turned on.</p></noscript></div>
<div id="authView" hidden>
  <div class="authwrap">
    <div class="authpitch">
      <h1>Claim your spot on the yard.</h1>
      <p>An account is free and takes a minute. Browsing and the patent files never need one.</p>
      <ul class="perks">
        <li><span class="pi">{icon("flag")}</span><div><b>Reserve patents</b><span>Hold up to 5 for 30 days so other builders know you're on them.</span></div></li>
        <li><span class="pi">{icon("spark")}</span><div><b>Keep your inventions</b><span>Save ideas from the studio to your bench and pick them up anywhere.</span></div></li>
        <li><span class="pi">{icon("shield")}</span><div><b>Private by default</b><span>No ads, no tracking. Only your display name shows next to what you reserve.</span></div></li>
      </ul>
    </div>
    <div class="authcard" id="authCard">
      <div id="authMain">
        <h2 id="authTitle">Welcome back</h2><p class="sub" id="authSub">Sign in to your bench.</p>
        <div class="seg" role="tablist" aria-label="Account"><span class="ind" aria-hidden="true"></span><button type="button" role="tab" data-mode="in" aria-selected="true">Sign in</button><button type="button" role="tab" data-mode="up" aria-selected="false">Create account</button></div>
        <div id="oauthRow" hidden><button class="gbtn" type="button" id="googleBtn">{g}<span>Continue with Google</span></button><div class="ordiv">or with email</div></div>
        <form id="authForm" class="authform" novalidate>
          <div class="fgroup" id="nameRow" hidden><label for="aName">Display name</label><input class="field" id="aName" maxlength="40" autocomplete="nickname" placeholder="Shown next to your reservations"></div>
          <div class="fgroup"><label for="aEmail">Email</label><input class="field" id="aEmail" type="email" required autocomplete="email" placeholder="you@example.com"></div>
          <div class="fgroup" id="pwRow"><label for="aPw">Password</label><div class="pwbox"><input class="field" id="aPw" type="password" minlength="8" required autocomplete="current-password"><button type="button" id="pwShow" aria-pressed="false">Show</button></div>
            <div class="meterbar" id="pwMeter" hidden><i></i></div><small id="pwHint" hidden>At least 8 characters. A short phrase is easiest to remember.</small></div>
          <button class="btn primary lg" type="submit" id="authSubmit"><span>Sign in</span></button>
          <p class="status authstatus" id="authStatus" aria-live="polite"></p>
          <button class="btn quiet sm self-center" type="button" id="forgotBtn">Forgot your password?</button>
        </form>
      </div>
      <div id="authDone" hidden></div>
      <p class="fine2">By continuing you agree to the <a href="/legal/terms/">terms</a> and <a href="/legal/privacy/">privacy notice</a>.</p>
    </div>
  </div>
</div>
<div id="newPwView" hidden>
  <div class="authcard authsolo"><h2>Set a new password</h2><p class="sub">Choose a new password for your account.</p><form id="newPwForm" class="authform"><div class="fgroup"><label for="npw">New password</label><input class="field" id="npw" type="password" minlength="8" required autocomplete="new-password"></div><button class="btn primary lg" type="submit"><span>Save password</span></button><p class="status" id="npwStatus" aria-live="polite"></p></form></div>
</div>
<div id="benchView" hidden>
  <div id="welcome"></div>
  <div class="sechead"><div><h1>My bench</h1><p id="benchWho"></p></div><div class="rowbtns"><a class="btn primary" href="/studio/">{icon("spark")}New invention</a><a class="btn secondary" href="/settings/">{icon("gear")}Settings</a><button class="btn quiet" type="button" id="signOut">Sign out</button></div></div>
  <div class="explain"><span class="badge reserved">Reserved</span><p><b>What reserving does.</b> A reservation holds a patent for you on Patent Yard for 30 days. Other builders see it's taken, with your optional note, so nobody here duplicates your work. You can hold 5 at a time and renew in the last week. <b>It doesn't stop anyone from using the patent.</b> It gives you no legal rights: the invention stays free for everyone, including other builders.</p></div>
  <div class="bench">
    <div class="list"><header><h2>Reserved</h2><span class="badge plain" id="resCount">0 of 5</span></header><div id="resList"></div></div>
    <div class="list"><header><h2>Inventions</h2><span class="badge plain" id="ideaCount">0</span></header><div id="ideaList"></div></div>
  </div>
</div>
<div id="offView" hidden><div class="empty"><b>Your account didn't load</b><p>Check your connection or any content blocker, then reload. Browsing, the patent files and the invention studio work without an account.</p></div></div>
</div>"""
        self.page("/account/", "My account", "Sign in to reserve patents and keep your inventions on your Patent Yard bench.", body, section="/account/", scripts=("account",), index=False)

    def settings(self):
        def seg(name, opts):
            return (f'<div class="seg inline" role="radiogroup" aria-label="{E(name)}" data-setting="{name}">'
                    + "".join(f'<button type="button" role="radio" aria-checked="false" data-value="{v}">{E(t)}</button>' for v, t in opts) + "</div>")
        body = f"""<div class="page">
<div class="settings">
  <div class="sechead"><div><h1>Settings</h1><p>Display settings are saved in this browser. Account settings follow your account everywhere.</p></div></div>
  <section class="panel" aria-labelledby="sAppear"><h2 id="sAppear">Appearance</h2>
    <div class="setrow"><div><b>Theme</b><p>System follows your device's light or dark setting.</p></div>{seg("theme", [("system", "System"), ("light", "Light"), ("dark", "Dark")])}</div>
    <div class="setrow"><div><b>Drawings in dark mode</b><p>Original shows each sheet as published, black lines on paper; inverted turns them into light lines on the dark page.</p></div>{seg("drawings", [("original", "Original"), ("inverted", "Inverted")])}</div>
    <div class="setrow"><div><b>Text size</b><p>Makes everything on the site a little larger.</p></div>{seg("text", [("normal", "Normal"), ("large", "Large")])}</div>
    <div class="setrow"><div><b>Motion</b><p>Turns off animations, including the drawing plotter on the home page.</p></div>{seg("motion", [("system", "System"), ("reduce", "Reduce")])}</div>
  </section>
  <section class="panel" aria-labelledby="sBrowse"><h2 id="sBrowse">Browsing</h2>
    <div class="setrow"><div><b>Default order</b><p>How the register is sorted when you aren't searching. Recommended puts patents with a written summary and an easy build first.</p></div>{seg("sort", [("build", "Recommended"), ("recent", "Recently freed"), ("added", "Newly added")])}</div>
  </section>
  <section class="panel" aria-labelledby="sAcct"><h2 id="sAcct">Account</h2>
    <div id="acctOff" hidden><p class="muted pad-y">Account settings didn't load. Reload the page to try again.</p></div>
    <div id="acctOut" hidden><div class="setrow"><div><b>Not signed in</b><p>Sign in to reserve patents and keep inventions on your bench.</p></div><a class="btn primary" href="/account/?next=/settings/">Sign in</a></div></div>
    <div id="acctIn" hidden>
      <div class="setrow"><div><b>Email</b><p id="setEmail"></p></div></div>
      <form class="setrow" id="nameForm"><div><b><label for="setName">Display name</label></b><p>Shown next to the patents you reserve. Leave it blank to appear as "A builder".</p><input class="field narrow-input" id="setName" maxlength="40"></div><div class="rowbtns"><button class="btn secondary" type="submit">Save name</button></div></form>
      <form class="setrow" id="pwForm"><div><b><label for="setPw">New password</label></b><p>At least 8 characters.</p><input class="field narrow-input" id="setPw" type="password" minlength="8" autocomplete="new-password"></div><div class="rowbtns"><button class="btn secondary" type="submit">Change password</button></div></form>
      <div class="setrow"><div><b>Sign out</b><p>Signs you out in this browser.</p></div><button class="btn secondary" type="button" id="setSignOut">Sign out</button></div>
      <div class="setrow"><div><b>Delete account</b><p>Permanently removes your account, reservations and saved inventions.</p></div><button class="btn quiet" type="button" id="setDelete">Delete my account</button></div>
    </div>
    <p class="status" id="acctStatus" aria-live="polite"></p>
  </section>
  <section class="panel" aria-labelledby="sData"><h2 id="sData">Data in this browser</h2>
    <div class="setrow"><div><b>Clear saved settings and drafts</b><p>Resets the settings above and removes your unsent studio draft from this browser. Your account isn't affected.</p></div><button class="btn secondary" type="button" id="clearLocal">Clear</button></div>
  </section>
  <p class="muted note">Data checked against USPTO records {E(full_date(self.meta.get("verified") or self.meta["built"]))} · site version {self.version}</p>
</div></div>"""
        self.page("/settings/", "Settings", "Appearance, browsing and account settings for Patent Yard.", body, scripts=("settings",), index=False)
