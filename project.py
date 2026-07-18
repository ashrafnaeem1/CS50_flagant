"""
Flagant - Country Flags, Elegant. From India to the World.
A gui program that let's you type a country's name and shows its flag.
Country names and codes are fetched via pycountry module.
Flags are provided locally via ./flags folder, named with alpha2 codes.

Naming: Flag + Ele'gant' = Flagant.
Its supposed to show flags and be elegant at that.
Program Icon: an ant. A pun on the 'ant' part of Flag'ant'.
An Indian flag is shown in bg representing the Flag part of this app.

Note: This file is not intended to be imported by other files.
Note: You can change window size/position / flag size by quickly changing the
      constants below the imports, You can also change some colors that way.
"""


from typing import Optional
# Used to get path to the flag's directory.
from pathlib import Path

# -- Third-party imports --
# I am using mypy, flake8, pylint and pylance to keep code clean.
# customtkinter does not have any stubs for mypy, hence used type ignore
# using customtkinter instead of tkinter out of plain curiosity.
import customtkinter as ctk  # type: ignore[import-untyped]

# for country names and codes (alpha2), alpha2 needed for identifying flags
import pycountry

# for opening the flag image file in the ctk app.
from PIL import Image

# for fuzzy search
from rapidfuzz import process, fuzz

# -- Changable constants. In case you don't like some choices. --
# Ratio fixed. Change height to change sizes.
WINDOW_HEIGHT = 720         # Ratio is 1024:720 width:height
FLAG_DISPLAY_HEIGHT = 160   # Ratio is 240:160 width:height
# Window Position. Origin refers to the top left corner of the window.
WINDOW_ORIGIN_X = 0
WINDOW_ORIGIN_Y = 0
# Colors
ACCENT_COLOR = "#00e5ff"
SUGGESTIONS_BG = "#dddddd"
SUGGESTION_FG = "#eeeeec"
SUGGESTION_HOVER = "#caeaf0"
SUGGESTION_TEXT = "#040f24"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the program."""
    app = FlagantApp()
    app.mainloop()


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class FlagantApp(ctk.CTk):
    """The app is called 'Flagant'."""

    # --- Constants ---
    # we are using very simple sizing rather than dynamic.
    # This is to keep project as simple as possible.
    _PROGRAM_TITLE = "Flagant - Country Flags, elegant."
    _WINDOW_WIDTH_TO_HEIGHT_RATIO = 1024 / 720
    _WINDOW_HEIGHT = WINDOW_HEIGHT
    _WINDOW_WIDTH = round(_WINDOW_HEIGHT *
                          _WINDOW_WIDTH_TO_HEIGHT_RATIO)
    _WINDOW_ORIGIN_X = WINDOW_ORIGIN_X
    _WINDOW_ORIGIN_Y = WINDOW_ORIGIN_Y
    _DEFAULT_PAD = 20
    _NUM_TOTAL_WIN_COLUMNS = 2
    _MAX_SUGGESTIONS = 5
    _FLAG_DISPLAY_WIDTH_TO_HEIGHT_RATIO = 240 / 160
    _FLAG_DISPLAY_HEIGHT = FLAG_DISPLAY_HEIGHT
    _FLAG_DISPLAY_WIDTH = round(FLAG_DISPLAY_HEIGHT *
                                _FLAG_DISPLAY_WIDTH_TO_HEIGHT_RATIO)
    _FLAG_DISPLAY_SIZE = (_FLAG_DISPLAY_WIDTH,
                          FLAG_DISPLAY_HEIGHT)

    _ACCENT_COLOR = ACCENT_COLOR
    _SUGGESTIONS_BG = SUGGESTIONS_BG
    _SUGGESTION_FG = SUGGESTION_FG
    _SUGGESTION_HOVER = SUGGESTION_HOVER
    _SUGGESTION_TEXT = SUGGESTION_TEXT

    # --- Main Logic ---
    def __init__(self) -> None:
        """Configuration and initialisation."""
        super().__init__()
        # I have coded it in light mode and in my very humble opinion
        # adding a dark mode would make it more complex.
        ctk.set_appearance_mode("light")

        # iconbitmap with a .ico file works on Windows, but Tk on Linux/Mac
        # traditionally expects the older XBM bitmap format here and can
        # raise a TclError on a modern .ico. The icon is cosmetic, so a
        # missing/unsupported one shouldn't take the whole app down.
        try:
            # I created this icon by myself.
            # Its a ant with Indian Flag colors in the background. (from India)
            self.iconbitmap("favicon.ico")
        # fails on cs50.dev, works on my windows 11 laptop.
        # it is mostly a OS specific problem, ignoring others for simplicity.
        # I think the problem is with the file being an .ico file.
        # so this is an issue with cs50.dev (linux ig).
        except Exception:  # pylint: disable=broad-except
            # let the program continue even if you can't load the icon.
            pass
        self.title(self._PROGRAM_TITLE)
        self.geometry(
            "{w}x{h}+{x}+{y}"  # pylint: disable=consider-using-f-string
            .format(
                w=self._WINDOW_WIDTH,
                h=self._WINDOW_HEIGHT,
                x=self._WINDOW_ORIGIN_X,
                y=self._WINDOW_ORIGIN_Y
            ))
        for col in range(self._NUM_TOTAL_WIN_COLUMNS):
            # makes the columns a bit more responsive
            self.columnconfigure(col, weight=1)

        self.countries = load_countries()
        self.selected_country: Optional[dict] = None
        self.suggestion_buttons: list[ctk.CTkButton] = []
        self.current_matches: list[dict] = []

        # make/build all the components.
        self._build_title()
        self._build_search()
        self._build_suggestions_area()
        self._build_flag_display()

    # --- Widget builders ---
    def _build_title(self) -> None:
        label = ctk.CTkLabel(master=self)
        label.configure(text=self._PROGRAM_TITLE, font=("Verdana", 48))
        label.grid(row=0,
                   column=0,
                   padx=self._DEFAULT_PAD,
                   pady=self._DEFAULT_PAD,
                   sticky="new",
                   columnspan=self._NUM_TOTAL_WIN_COLUMNS)

    def _build_search(self) -> None:
        self.search_entry = ctk.CTkEntry(
            master=self,
            placeholder_text="Type a country name...",
            font=("Merriweather", 22), height=36
        )
        self.search_entry.grid(row=1,
                               column=0,
                               padx=self._DEFAULT_PAD,
                               pady=(0, self._DEFAULT_PAD),
                               sticky="ew",
                               columnspan=self._NUM_TOTAL_WIN_COLUMNS)

        # CTkEntry + KeyRelease lets us re-run fuzzy_search on every
        # keystroke and update the suggestion list live.
        self.search_entry.bind("<KeyRelease>", self._on_key_release)
        # "Hit enter to search" (see module docstring): select the current
        # top suggestion, same as clicking its button.
        self.search_entry.bind("<Return>", self._on_enter_pressed)

    def _build_suggestions_area(self) -> None:
        self.suggestions_frame = ctk.CTkFrame(master=self,
                                              fg_color=self._SUGGESTIONS_BG,
                                              corner_radius=8,
                                              border_width=1,
                                              border_color=self._ACCENT_COLOR)
        self.suggestions_frame.columnconfigure(0, weight=1)
        # Not gridded here on purpose. An empty CTkFrame still renders its
        # background/border regardless of whether it has children, so
        # gridding it up front showed as an empty bordered box before
        # typing anything. It's only grid()'d in _on_key_release once there
        # are actual suggestion buttons inside it, and grid_remove()'d
        # again in _clear_suggestions (covers empty query, no matches, and
        # right after a country gets selected).

    def _build_flag_display(self) -> None:
        self.flag_label = ctk.CTkLabel(master=self, text="")
        self.flag_label.grid(row=3,
                             column=0,
                             padx=self._DEFAULT_PAD,
                             pady=self._DEFAULT_PAD,
                             sticky="n",
                             columnspan=self._NUM_TOTAL_WIN_COLUMNS)

    # --- Event handlers ---
    def _on_key_release(self,
                        event=None) -> None:  # pylint: disable=unused-argument
        """Live search feature, update results after every keystroke entry."""
        query = self.search_entry.get()
        # remove the suggestion frame.
        self._clear_suggestions()
        if not query.strip():
            return
        # the actual search.
        matches = fuzzy_search(query, self.countries,
                               limit=self._MAX_SUGGESTIONS)
        self.current_matches = matches
        # zero matches.
        if not matches:
            return
        # draw the suggestion frame.
        self.suggestions_frame.grid(row=2,
                                    column=0,
                                    padx=self._DEFAULT_PAD,
                                    sticky="new",
                                    columnspan=self._NUM_TOTAL_WIN_COLUMNS)
        self._create_buttons(matches=matches)

    def _create_buttons(self, matches) -> None:
        # creates all the buttons
        for i, country in enumerate(matches):
            btn = ctk.CTkButton(
                master=self.suggestions_frame,
                text=country["name"],
                anchor="w",  # align to left.
                fg_color=self._SUGGESTION_FG,
                hover_color=self._SUGGESTION_HOVER,
                text_color=self._SUGGESTION_TEXT,
                corner_radius=6,
                command=lambda c=country: self._select_country(c),
            )
            btn.grid(row=i, column=0, sticky="ew",
                     padx=6, pady=(6 if i == 0 else 2))
            self.suggestion_buttons.append(btn)

    def _clear_suggestions(self) -> None:
        # destroy all buttons
        for btn in self.suggestion_buttons:
            btn.destroy()
        # empty button list
        self.suggestion_buttons.clear()
        # remove suggestion frame BUT keep the configuration (for future).
        self.suggestions_frame.grid_remove()
        # reset search matches
        self.current_matches = []

    def _on_enter_pressed(
            self,
            # every ctk event handler must have an event argument, even unused.
            event=None) -> None:  # pylint: disable=unused-argument
        """Hit Enter to pick current top suggestion, same as clicking it."""
        if self.current_matches:
            self._select_country(self.current_matches[0])

    def _select_country(self, country: dict) -> None:
        self.selected_country = country
        self._on_country_select(country)

    def _on_country_select(self, country: dict) -> None:
        # -- Phase 1: Suggestions --
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, country["name"])
        self._clear_suggestions()

        # -- Phase 2: Main logic --
        self._show_flag(country)

    def _show_flag(self, country: dict) -> None:
        flag_path = get_flag_path(country["alpha2"])
        if flag_path is None:
            self.flag_label.configure(image=None, text="(no flag available)")
            return
        pil_image = Image.open(flag_path)
        ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image,
                                 size=self._FLAG_DISPLAY_SIZE)
        self.flag_label.configure(image=ctk_image,
                                  text="")


# --- Helpers ---
# Data helpers — Independent of GUI and only handle the business logic.
# testable via pytests, see test_project.py
def load_countries() -> list[dict[str, str]]:
    """
    Return a list of dicts: [{"name": "Germany", "alpha2": "DE"}, ...]
    """
    countries: list[dict[str, str]] = []
    # Pulled entirely from the offline pycountry database.
    for c in pycountry.countries:
        countries.append({"name": c.name, "alpha2": c.alpha_2})
    return countries


def fuzzy_search(query: str,
                 countries: list[dict[str, str]],
                 limit=5):
    """
    Given partial/typo'd text, return up to `limit` best-matching country
    dicts from `countries`, best match first. Returns [] for empty query.
    This is the hardest part of the app.

    Two-tier strategy:
      1. Prefix/substring matches first (handles normal correct typing,
         e.g. "fra" -> France, "United" -> all the United ___ countries).
      2. Fuzzy fallback fills any remaining slots (catches typos,
         e.g. "jermany" -> Germany).
    """
    if not query.strip():
        return []

    # lowercase the query.
    query = query.lower()
    # get a dict of entries of country_name : country_dict
    name_to_country = {c["name"]: c for c in countries}

    # Tier 1: substring matches, prefix matches ranked above mid-word matches
    substring_hits = [c for c in countries if query in c["name"].lower()]
    substring_hits.sort(
        key=lambda c: (
            # it took me time to get this through my head myself:
            # False is zero (0), True is one (1). 0 (False) comes before
            # 1 (True) by that logic, if starts with query -> True.
            # But True (1) comes after, not first, so we do a 'not' on that
            # True to make it False (0). since False comes before true:
            # "if starts with query" comes first.
            # Hence results are sorted with the starting part of their names.
            not c["name"].lower().startswith(query),
            # Now countries having same status (same startswith) will be
            # sorted alphabatically.
            c["name"]
        )
    )
    results = substring_hits[:limit]

    # Tier 2: fuzzy fallback for anything still missing (typo tolerance)
    if len(results) < limit:
        # set of already found results. Preferred, Sets are faster than lists.
        already: set[str] = {c["name"] for c in results}
        remaining_names = [c["name"]
                           for c in countries if c["name"] not in already]
        need = limit - len(results)
        fuzzy_matches = process.extract(
            query, remaining_names, scorer=fuzz.WRatio, limit=need)

        # Only include fuzzy matches with a score of 60 or higher
        # m[0] = country name in fuzzy_matches, m[1] = similarity score (0-100)
        results += [
            name_to_country[m[0]]
            for m in fuzzy_matches
            if m[1] >= 60
        ]

    return results


def get_flag_path(alpha2: str, flags_dir="flags") -> str | None:
    """
    Return the local file path to a country's flag PNG, or None if
    that country's flag isn't in the bundled set (rare edge cases, e.g.
    territories without a distinct flag file).
    """
    path = Path(flags_dir) / f"{alpha2.lower()}.png"
    return str(path) if path.exists() else None


if __name__ == "__main__":
    main()
