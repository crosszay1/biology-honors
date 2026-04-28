import curses

def main(stdscr):
    curses.curs_set(1)
    stdscr.clear()

    height, width = stdscr.getmaxyx()

    # Split screen: top = output, bottom = input
    output_h = height - 3
    input_h = 3

    output_win = curses.newwin(output_h, width, 0, 0)
    input_win = curses.newwin(input_h, width, output_h, 0)

    output_win.scrollok(True)
    input_win.border()

    log_lines = []

    def log(msg):
        log_lines.append(msg)
        output_win.clear()

        # Show only visible lines
        max_lines = output_h - 1
        visible = log_lines[-max_lines:]

        for i, line in enumerate(visible):
            output_win.addstr(i, 0, line)

        output_win.refresh()

    def get_input(prompt="> "):
        input_win.clear()
        input_win.border()
        input_win.addstr(1, 1, prompt)
        input_win.refresh()

        curses.echo()
        user_input = input_win.getstr(1, len(prompt) + 1).decode("utf-8")
        curses.noecho()

        return user_input

    # Demo loop
    log("Console started.")
    while True:
        cmd = get_input()

        if cmd.lower() in ("exit", "quit"):
            break

        log(f"> {cmd}")
        log(f"Echo: {cmd}")

curses.wrapper(main)