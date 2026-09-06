# -*- coding: utf-8 -*-
# gitinfo.py — detects which git branch the running program was started
# from, so the UI can warn tydeligt when man kører en udviklingsgren i
# stedet for den officielle master-branch (se ui/status_view.py og
# ui/shell.py).
from pathlib import Path

MASTER_BRANCHES = {"master", "main"}


def get_branch_name():
    """Navnet på den branch, programmet reelt følger, eller None hvis det
    ikke kan bestemmes (intet git-repo, git ikke installeret, detached
    HEAD).

    Bruger upstream-branchen (fx "origin/feature/x") frem for det lokale
    branch-navn, når den findes. Det lokale navn kan ikke stoles på alene:
    en installeret kopi kan sagtens have en lokal branch der hedder
    "master", men som reelt tracker fx origin/feature/kryptering-lokale-data
    (fx sat op af et deploy-script). I det tilfælde ville det lokale navn
    fejlagtigt få programmet til at tro det kører den officielle master."""
    base_dir = Path(__file__).resolve().parent
    try:
        import git
        repo = git.Repo(base_dir, search_parent_directories=True)
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
