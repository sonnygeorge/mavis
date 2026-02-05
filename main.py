#!/usr/bin/env python
from dotenv import load_dotenv

from mavis.mavis import run
from mavis.llm import OpenAILLM
from mavis.schema import ActionScene, RelativeWhere

load_dotenv()


def main():
    llm = OpenAILLM(model="gpt-5.2-2025-12-11")
    action_scene = ActionScene(
        who="person",
        does="flies",
        what=None,
        where=RelativeWhere(preposition="over", what="laptop"),
        to_whom="tree",
    )
    output_images = run(llm, action_scene)


if __name__ == "__main__":
    main()
