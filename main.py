#!/usr/bin/env python
from dotenv import load_dotenv

from mavis.mavis import run
from mavis.vlm import OpenAIVLM
from mavis.schema import ActionScene, RelativeWhere

load_dotenv()


def main():
    vlm = OpenAIVLM(model="gpt-5.2-2025-12-11")
    # action_scene = ActionScene(
    #     who="person",
    #     does="tosses",
    #     what="chair",
    #     where=RelativeWhere(preposition="over", what="sign"),
    #     to_whom="basketball",
    # )
    # action_scene = ActionScene(
    #     who="bird",
    #     does="chases",
    #     what="puma",
    #     where=None,
    #     to_whom=None,
    # )
    action_scene = ActionScene(
        who="person",
        does="throws",
        what="violin",
        where=None,
        to_whom="dog",
    )

    output_images = run(vlm, action_scene)


if __name__ == "__main__":
    main()
