import argparse

BLANK = " "
ALPHABET = {"{", "}", "|"}

ZERO = "{|}"


def only_allowed_symbols(s: str) -> bool:
    return all(ch in ALPHABET for ch in s)


def surreal_successor(s: str) -> str:
    # +1 as surreal operation: x + 1 = {x|}
    return "{" + s + "|}"


def surreal_predecessor(s: str) -> str:
    # -1 as surreal operation: x - 1 = {|x}
    return "{|" + s + "}"


def is_zero(s: str) -> bool:
    return s == ZERO


def is_successor_form(s: str) -> bool:
    return (
        s.startswith("{")
        and s.endswith("|}")
        and not s.startswith("{|")
        and s != ZERO
    )


def is_predecessor_form(s: str) -> bool:
    return s.startswith("{|") and s.endswith("}") and s != ZERO


def inner_successor(s: str) -> str:
    # removes outer { x | }
    return s[1:-2]


def inner_predecessor(s: str) -> str:
    # removes outer { | x }
    return s[2:-1]


def is_valid_surreal_integer(s: str) -> bool:
    if not s:
        return False

    if not only_allowed_symbols(s):
        return False

    if is_zero(s):
        return True

    if is_successor_form(s):
        return is_valid_surreal_integer(inner_successor(s))

    if is_predecessor_form(s):
        return is_valid_surreal_integer(inner_predecessor(s))

    return False


def compare_surreal(a: str, b: str, trace=False) -> str:
    """
    Compares canonical finite surreal integers without converting to int.

    Rules:
    0 = {|}
    successor(x) = {x|}
    predecessor(x) = {|x}
    """

    if not is_valid_surreal_integer(a):
        raise ValueError("First surreal number is invalid")

    if not is_valid_surreal_integer(b):
        raise ValueError("Second surreal number is invalid")

    while True:
        if trace:
            print(f"Comparing: {a}  ?  {b}")

        if a == b:
            return "="

        if is_zero(a):
            return ">" if is_predecessor_form(b) else "<"

        if is_zero(b):
            return "<" if is_predecessor_form(a) else ">"

        if is_successor_form(a) and is_predecessor_form(b):
            return ">"

        if is_predecessor_form(a) and is_successor_form(b):
            return "<"

        if is_successor_form(a) and is_successor_form(b):
            a = inner_successor(a)
            b = inner_successor(b)
            continue

        if is_predecessor_form(a) and is_predecessor_form(b):
            a = inner_predecessor(a)
            b = inner_predecessor(b)
            continue

        raise ValueError("Unexpected comparison structure")


def generate_canonical_surreal_integers(limit: int):
    values = [ZERO]

    current = ZERO
    positives = []
    for _ in range(limit):
        current = surreal_successor(current)
        positives.append(current)

    current = ZERO
    negatives = []
    for _ in range(limit):
        current = surreal_predecessor(current)
        negatives.append(current)

    return list(reversed(negatives)) + values + positives

def surreal_to_signed_int_tape(s: str) -> str:
    """
    TM-style surreal -> integer tape.

    Output format:
    {|}          -> 0
    {{|}|}       -> +
    {{{|}|}|}    -> ++
    {|{|}}       -> -
    {|{|{|}}}    -> --
    """

    if not is_valid_surreal_integer(s):
        raise ValueError("Invalid surreal integer")

    tape = ""

    while not is_zero(s):
        if is_successor_form(s):
            tape += "+"
            s = inner_successor(s)

        elif is_predecessor_form(s):
            tape += "-"
            s = inner_predecessor(s)

        else:
            raise ValueError("Invalid surreal structure")

    if tape == "":
        return "0"

    return tape


def signed_int_tape_to_surreal(tape: str) -> str:
    """
    TM-style integer tape -> surreal.

    Input format:
    0   -> {|}
    +   -> {{|}|}
    ++  -> {{{|}|}|}
    -   -> {|{|}}
    --  -> {|{|{|}}}
    """

    if tape == "0":
        return ZERO

    if not tape:
        raise ValueError("Empty integer tape")

    result = ZERO

    for symbol in tape:
        if symbol == "+":
            result = surreal_successor(result)
        elif symbol == "-":
            result = surreal_predecessor(result)
        else:
            raise ValueError("Integer tape must contain only 0, +, or -")

    return result

def main():
    parser = argparse.ArgumentParser(
        description="Symbolic Turing-machine-style operations on finite surreal integers"
    )

    parser.add_argument("--validate", help="Validate a finite canonical surreal integer")
    parser.add_argument("--successor", help="Apply surreal +1 operation")
    parser.add_argument("--predecessor", help="Apply surreal -1 operation")
    parser.add_argument("--compare", nargs=2, help="Compare two surreal integers structurally")
    parser.add_argument("--generate-cfg", type=int, help="Generate surreal integers up to depth n")
    parser.add_argument("--trace", action="store_true", help="Show comparison trace")
    parser.add_argument("--to-int", help="Convert surreal integer to signed integer tape")
    parser.add_argument("--to-surreal", help="Convert signed integer tape to surreal integer")

    args = parser.parse_args()

    if args.validate:
        print("Input:", args.validate)
        print("Result:", "ACCEPT" if is_valid_surreal_integer(args.validate) else "REJECT")

    elif args.successor:
        if not is_valid_surreal_integer(args.successor):
            print("Invalid surreal integer")
            return

        result = surreal_successor(args.successor)
        print("Input:", args.successor)
        print("Successor:", result)

    elif args.predecessor:
        if not is_valid_surreal_integer(args.predecessor):
            print("Invalid surreal integer")
            return

        result = surreal_predecessor(args.predecessor)
        print("Input:", args.predecessor)
        print("Predecessor:", result)

    elif args.compare:
        a, b = args.compare

        result = compare_surreal(a, b, trace=args.trace)
        print(f"{a} {result} {b}")

    elif args.generate_cfg is not None:
        values = generate_canonical_surreal_integers(args.generate_cfg)

        print("CFG-generated canonical finite surreal integers:")
        for value in values:
            print(value)
    elif args.to_int:
        try:
            result = surreal_to_signed_int_tape(args.to_int)
            print("Input surreal:", args.to_int)
            print("Integer tape:", result)
        except ValueError as e:
            print("Error:", e)

    elif args.to_surreal:
        try:
            result = signed_int_tape_to_surreal(args.to_surreal)
            print("Input integer tape:", args.to_surreal)
            print("Surreal:", result)
        except ValueError as e:
            print("Error:", e)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()