# -*- coding: utf-8 -*-
# gitinfo.py — detects which git branch the running program was started
# from, so the UI can warn tydeligt when man kører en udviklingsgren i
# stedet for den officielle master-branch (se ui/status_view.py og
# ui/shell.py).
from pathlib import Path

MASTER_BRANCHES = {"master", "main"}


def get_branch_name():
    """Navnet på den branch, programmets indhold reelt svarer til, eller
    None hvis det ikke kan bestemmes (intet git-repo, git ikke installeret,
    ingen origin, eller lokale commits der ikke matcher nogen kendt
    origin-branch).

    Hverken det lokale branch-navn eller dets upstream kan stoles på alene:
    launcher.pyw's opdateringsmekanisme laver "git fetch" + "git reset
    --hard origin/<branch>" på hvad end der er checket ud, uden at skifte
    branch. Så en installeret kopi kan sagtens stå på en lokal branch der
    hedder fx "claude_code" eller "master" — uden nogen upstream sat — men
    hvis dens commit rent faktisk matcher origin/master, kører den i
    praksis master, og omvendt. Vi finder derfor først den origin-branch
    hvis tip matcher den aktuelle commit (uafhængigt af det lokale navn),
    og falder kun tilbage til det lokale branch-navn/dets upstream, hvis
    ingen origin-branch matcher (dvs. der er lokale commits ud over det
    kendte)."""
    base_dir = Path(__file__).resolve().parent
    try:
        import git
        repo = git.Repo(base_dir, search_parent_directories=True)
        head_sha = repo.head.commit.hexsha

        try:
            origin_refs = list(repo.remotes.origin.refs)
        except Exception:
            origin_refs = []
        matches = [r.remote_head for r in origin_refs if r.commit.hexsha == head_sha]
        if matches:
            for name in matches:
                if name.lower() in MASTER_BRANCHES:
                    return name
            return matches[0]

        active = repo.active_branch
        tracking = active.tracking_branch()
        if tracking is not None:
            return tracking.remote_head
        return active.name
    except Exception:
        return None


def is_non_master_branch():
    """True hvis programmet kører fra en anden branch end master/main —
    dvs. en udviklingsversion, der ikke bør forveksles med den officielle.
    False hvis branch er master/main, eller hvis branch ikke kan bestemmes
    (fx detached HEAD ved en release-tag — kan ikke skelnes sikkert fra en
    udviklingskørsel, så vi advarer ikke i det tilfælde)."""
    branch = get_branch_name()
    return bool(branch) and branch.lower() not in MASTER_BRANCHES
