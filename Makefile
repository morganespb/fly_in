VENV		= .venv
PYTHON		= $(VENV)/bin/python
MAIN		= fly_in.py
MAP			?= src/maps/easy/01_linear_path.txt
MYPY_FLAGS	= --warn-return-any --warn-unused-ignores --ignore-missing-imports \
			  --disallow-untyped-defs --check-untyped-defs

RESET		= \033[0m
BOLD		= \033[1m
RED			= \033[31m
GREEN		= \033[32m
YELLOW		= \033[33m
CYAN		= \033[36m
BLUE2		= \033[38;5;39m
CYAN2		= \033[38;5;45m
TEAL		= \033[38;5;51m

TITLE		= @printf "$(BOLD)$(CYAN)==>$(RESET) $(BOLD)%s$(RESET)\n"
OK			= @printf "$(GREEN)✔ %s$(RESET)\n"

.DEFAULT_GOAL	= help

logo:
	@printf "\n"
	@printf "$(BLUE2)%s$(RESET)\n" '    ███████╗██╗  ██╗   ██╗      ██╗███╗   ██╗'
	@printf "$(BLUE2)%s$(RESET)\n" '    ██╔════╝██║  ╚██╗ ██╔╝      ██║████╗  ██║'
	@printf "$(CYAN2)%s$(RESET)\n" '    █████╗  ██║   ╚████╔╝ █████╗██║██╔██╗ ██║'
	@printf "$(CYAN2)%s$(RESET)\n" '    ██╔══╝  ██║    ╚██╔╝  ╚════╝██║██║╚██╗██║'
	@printf "$(TEAL)%s$(RESET)\n"  '    ██║     ███████╗██║         ██║██║ ╚████║'
	@printf "$(TEAL)%s$(RESET)\n"  '    ╚═╝     ╚══════╝╚═╝         ╚═╝╚═╝  ╚═══╝'
	@printf "\n$(YELLOW)%s$(RESET)  $(BOLD)%s$(RESET)  $(YELLOW)%s$(RESET)\n\n" \
		'-=(o)=-' 'Drones are interesting.' '-=(o)=-'

help: logo
	@printf "$(BOLD)$(CYAN)Fly-in$(RESET) - available rules:\n"
	@printf "  $(YELLOW)%-12s$(RESET) %s\n" \
		"install"     "install dependencies" \
		"run"         "run the simulation  (MAP=path/to/map.txt)" \
		"debug"       "run under pdb       (MAP=path/to/map.txt)" \
		"clean"       "remove caches" \
		"fclean"      "remove caches + venv" \
		"re"          "fclean + install" \
		"lint"        "flake8 + mypy" \
		"lint-strict" "flake8 + mypy --strict"

$(VENV)/bin/activate: requirements.txt
	$(TITLE) "Creating the virtual environment in $(VENV)"
	@python3 -m venv $(VENV)
	@$(PYTHON) -m pip install --quiet --upgrade pip
	@$(PYTHON) -m pip install --quiet -r requirements.txt
	@touch $(VENV)/bin/activate
	$(OK) "Dependencies installed (flake8, mypy, pytest, pygame-ce)"

install: $(VENV)/bin/activate
	$(OK) "Environment ready in $(VENV)"

run: $(VENV)/bin/activate
	$(TITLE) "Running $(MAIN) on $(MAP)"
	@$(PYTHON) $(MAIN) $(MAP)

debug: $(VENV)/bin/activate
	$(TITLE) "Debugging $(MAIN) on $(MAP) (type 'c' to continue, 'q' to quit)"
	@$(PYTHON) -m pdb $(MAIN) $(MAP)

clean:
	$(TITLE) "Cleaning caches"
	@rm -rf .mypy_cache .pytest_cache
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	$(OK) "Clean"

fclean: clean
	$(TITLE) "Removing $(VENV)"
	@rm -rf $(VENV)
	$(OK) "Full clean"

re: fclean install

lint: $(VENV)/bin/activate
	$(TITLE) "flake8"
	@$(PYTHON) -m flake8 . && printf "$(GREEN)✔ flake8 OK$(RESET)\n" \
		|| (printf "$(RED)✘ flake8 failed$(RESET)\n"; exit 1)
	$(TITLE) "mypy"
	@$(PYTHON) -m mypy . $(MYPY_FLAGS) && printf "$(GREEN)✔ mypy OK$(RESET)\n" \
		|| (printf "$(RED)✘ mypy failed$(RESET)\n"; exit 1)

lint-strict: $(VENV)/bin/activate
	$(TITLE) "flake8"
	@$(PYTHON) -m flake8 . && printf "$(GREEN)✔ flake8 OK$(RESET)\n" \
		|| (printf "$(RED)✘ flake8 failed$(RESET)\n"; exit 1)
	$(TITLE) "mypy --strict"
	@$(PYTHON) -m mypy . --strict && printf "$(GREEN)✔ mypy strict OK$(RESET)\n" \
		|| (printf "$(RED)✘ mypy strict failed$(RESET)\n"; exit 1)


.PHONY: help install run debug clean fclean re lint lint-strict logo
