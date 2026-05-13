import argparse
from dataclasses import dataclass


BLANK = " "
ALPHABET = {"{", "}", "|"}


@dataclass
class TuringMachine:
    tape: list
    head: int
    state: str
    rules: dict
    blank: str = BLANK

    def step(self):
        symbol = self.tape[self.head]

        if (self.state, symbol) not in self.rules:
            self.state = "reject"
            return

        new_state, write_symbol, direction = self.rules[(self.state, symbol)]
        self.tape[self.head] = write_symbol

        if direction == "R":
            self.head += 1
            if self.head == len(self.tape):
                self.tape.append(self.blank)

        elif direction == "L":
            self.head -= 1
            if self.head < 0:
                self.tape.insert(0, self.blank)
                self.head = 0

        self.state = new_state

    def run(self, trace=False, max_steps=10000):
        steps = 0

        while self.state not in ["accept", "reject"]:
            if trace:
                print(self.snapshot())

            self.step()
            steps += 1

            if steps > max_steps:
                self.state = "reject"
                break

        if trace:
            print(self.snapshot())

        return self.state, "".join(self.tape)

    def snapshot(self):
        tape_str = "".join(self.tape)
        pointer = " " * self.head + "^"
        return f"{tape_str}\n{pointer} state={self.state}\n"


def only_allowed_symbols(s: str) -> bool:
    return all(ch in ALPHABET for ch in s)


def is_non_positive_finite_integer(s: str) -> bool:
    """
    Generates only:
    0, -1, -2, -3, ...

    0  = {|}
    -1 = {|{|}}
    -2 = {|{|{|}}}
    """

    if s == "{|}":
        return True

    if s.startswith("{|") and s.endswith("}"):
        inner = s[2:-1]
        return is_non_positive_finite_integer(inner)

    return False


def is_valid_surreal_integer(s: str) -> bool:
    """
    Valid canonical finite integer surreal numbers:

    0  = {|}
    1  = {{|}|}
    2  = {{{|}|}|}

    -1 = {|{|}}
    -2 = {|{|{|}}}
    """

    if not s:
        return False

    if not only_allowed_symbols(s):
        return False

    if s == "{|}":
        return True

    # positive integer: x + 1 = {x|}
    if s.startswith("{") and s.endswith("|}"):
        inner = s[1:-2]
        return is_valid_surreal_integer(inner)

    # negative integer: x - 1 = {|x}, where x <= 0
    if s.startswith("{|") and s.endswith("}"):
        inner = s[2:-1]
        return is_non_positive_finite_integer(inner)

    return False


def surreal_to_int(s: str) -> int:
    if not is_valid_surreal_integer(s):
        raise ValueError("Invalid finite integer surreal number")

    if s == "{|}":
        return 0

    # positive case: {x|}
    if s.startswith("{") and s.endswith("|}"):
        inner = s[1:-2]
        return surreal_to_int(inner) + 1

    # negative case: {|x}
    if s.startswith("{|") and s.endswith("}"):
        inner = s[2:-1]
        return surreal_to_int(inner) - 1

    raise ValueError("Invalid finite integer surreal number")


def surreal_to_unary(s: str) -> str:
    value = surreal_to_int(s)

    if value == 0:
        return "0"

    if value > 0:
        return "1" * value

    return "-" + ("1" * abs(value))


def compare_surreal(a: str, b: str) -> str:
    x = surreal_to_int(a)
    y = surreal_to_int(b)

    if x < y:
        return "<"
    elif x > y:
        return ">"
    return "="


def generate_canonical_surreal_integers(limit: int):
    """
    CFG for canonical finite integer surreal numbers:

    S → P | Z | N
    Z → {|}
    P → {Z|} | {P|}
    N → {|Z} | {|N}

    This generates all canonical finite integer surreal numbers
    from -limit to +limit.
    """

    values = {"{|}": 0}

    zero = "{|}"

    positive = zero
    for i in range(1, limit + 1):
        positive = "{" + positive + "|}"
        values[positive] = i

    negative = zero
    for i in range(1, limit + 1):
        negative = "{|" + negative + "}"
        values[negative] = -i

    return values


def build_convert_machine(input_string: str) -> TuringMachine:
    """
    Turing Machine that converts non-negative surreal integers to unary.

    {|}          -> =0
    {{|}|}       -> =1
    {{{|}|}|}    -> =11

    It ignores the first | because it belongs to the base number {|}.
    Every remaining | becomes one unary 1.
    """

    tape = list(input_string) + [BLANK]
    rules = {}

    def add(state, symbols, new_state, write=None, move="R"):
        if isinstance(symbols, str):
            symbols = [symbols]

        for sym in symbols:
            rules[(state, sym)] = (
                new_state,
                write if write is not None else sym,
                move,
            )

    add("start", "{", "goEnd", move="R")

    for sym in ["|", "}", "=", "1", "0", BLANK]:
        add("start", sym, "reject")

    for sym in ["{", "|", "}"]:
        add("goEnd", sym, "goEnd", move="R")
    add("goEnd", BLANK, "returnLeft", write="=", move="L")

    for sym in ["{", "|", "}", "=", "1", "0", "B"]:
        add("returnLeft", sym, "returnLeft", move="L")
    add("returnLeft", BLANK, "markFirstBar", move="R")

    add("markFirstBar", "{", "findFirstBar", move="R")

    for sym in ["|", "}", "=", "B", "1", "0", BLANK]:
        add("markFirstBar", sym, "reject")

    for sym in ["{", "}"]:
        add("findFirstBar", sym, "findFirstBar", move="R")
    add("findFirstBar", "|", "returnLeftCount", write="B", move="L")

    for sym in ["=", "B", "1", "0", BLANK]:
        add("findFirstBar", sym, "reject")

    for sym in ["{", "|", "}", "=", "B", "1", "0"]:
        add("returnLeftCount", sym, "returnLeftCount", move="L")
    add("returnLeftCount", BLANK, "countBars", move="R")

    for sym in ["{", "}", "B"]:
        add("countBars", sym, "countBars", move="R")

    add("countBars", "|", "appendOne", write="B", move="R")
    add("countBars", "=", "finish", move="R")

    for sym in ["1", "0", BLANK]:
        add("countBars", sym, "reject")

    for sym in ["{", "|", "}", "=", "B", "1", "0"]:
        add("appendOne", sym, "appendOne", move="R")
    add("appendOne", BLANK, "returnLeftCount", write="1", move="L")

    add("finish", "1", "accept", move="R")
    add("finish", BLANK, "accept", write="0", move="R")

    return TuringMachine(
        tape=tape,
        head=0,
        state="start",
        rules=rules,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Turing Machine framework for finite integer surreal numbers"
    )

    parser.add_argument("--validate", help="Validate one finite integer surreal number")
    parser.add_argument("--convert", help="Convert one finite integer surreal number to unary")
    parser.add_argument("--compare", nargs=2, help="Compare two finite integer surreal numbers")
    parser.add_argument("--generate-cfg", type=int, help="Generate surreal integers using CFG up to depth n")
    parser.add_argument("--trace", action="store_true", help="Show Turing Machine trace")

    args = parser.parse_args()

    if args.validate:
        valid = is_valid_surreal_integer(args.validate)

        print("Input:", args.validate)
        print("Result:", "ACCEPT" if valid else "REJECT")

        if valid:
            print("Integer value:", surreal_to_int(args.validate))

    elif args.convert:
        if not is_valid_surreal_integer(args.convert):
            print("Invalid surreal integer")
            return

        value = surreal_to_int(args.convert)
        unary = surreal_to_unary(args.convert)

        print("Input:", args.convert)
        print("Integer value:", value)
        print("Unary:", unary)

        if value >= 0:
            machine = build_convert_machine(args.convert)
            state, tape = machine.run(trace=args.trace)

            print("Turing Machine final state:", state)
            print("Turing Machine tape:", tape)
        else:
            print("Negative integer converted using recursive signed unary logic.")

    elif args.compare:
        a, b = args.compare

        if not is_valid_surreal_integer(a):
            print("First number is invalid")
            return

        if not is_valid_surreal_integer(b):
            print("Second number is invalid")
            return

        result = compare_surreal(a, b)

        print(f"{a} {result} {b}")
        print(f"{surreal_to_int(a)} {result} {surreal_to_int(b)}")

    elif args.generate_cfg is not None:
        values = generate_canonical_surreal_integers(args.generate_cfg)

        print(
            f"CFG-generated canonical surreal integers "
            f"from -{args.generate_cfg} to {args.generate_cfg}:"
        )

        for surreal, value in sorted(values.items(), key=lambda item: item[1]):
            print(f"{value:3} = {surreal}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()