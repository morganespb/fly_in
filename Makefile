PYTHON		= python3
MAIN		= fly_in.py
MAP			?= maps/easy/01_linear_path.txt
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

help: logo
	@printf "$(BOLD)$(CYAN)Fly-in$(RESET) - available rules:\n"
	@printf "  $(YELLOW)%-12s$(RESET) %s\n" \
		"install"     "install dependencies" \
		"run"         "run the simulation  (MAP=path/to/map.txt)" \
		"debug"       "run under pdb       (MAP=path/to/map.txt)" \
		"clean"       "remove caches" \
		"lint"        "flake8 + mypy" \
		"lint-strict" "flake8 + mypy --strict"

install:
	$(TITLE) "Installing dependencies"
	@$(PYTHON) -m pip install -r requirements.txt
	$(OK) "Dependencies installed"

run:
	$(TITLE) "Running $(MAIN) on $(MAP)"
	@$(PYTHON) $(MAIN) $(MAP)

debug:
	$(TITLE) "Debugging $(MAIN) on $(MAP) (type 'c' to continue, 'q' to quit)"
	@$(PYTHON) -m pdb $(MAIN) $(MAP)

clean:
	$(TITLE) "Cleaning caches"
	@rm -rf .mypy_cache .pytest_cache
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	$(OK) "Clean"

lint:
	$(TITLE) "flake8"
	@flake8 . && printf "$(GREEN)✔ flake8 OK$(RESET)\n" \
		|| (printf "$(RED)✘ flake8 failed$(RESET)\n"; exit 1)
	$(TITLE) "mypy"
	@mypy . $(MYPY_FLAGS) && printf "$(GREEN)✔ mypy OK$(RESET)\n" \
		|| (printf "$(RED)✘ mypy failed$(RESET)\n"; exit 1)

lint-strict:
	$(TITLE) "flake8"
	@flake8 . && printf "$(GREEN)✔ flake8 OK$(RESET)\n" \
		|| (printf "$(RED)✘ flake8 failed$(RESET)\n"; exit 1)
	$(TITLE) "mypy --strict"
	@mypy . --strict && printf "$(GREEN)✔ mypy strict OK$(RESET)\n" \
		|| (printf "$(RED)✘ mypy strict failed$(RESET)\n"; exit 1)


.PHONY: help install run debug clean lint lint-strict logo
