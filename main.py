#!/usr/bin/env python
from dotenv import load_dotenv

from mavis.mavis import run
from mavis.vlm import OpenAIVLM
from mavis.schema import ActionScene, RelativeWhere

load_dotenv()


# Atypical compositions of action arguments where:
# - The arguments are physical objects/entities in data/objaverse/shapes
# - The objects/entities do not need to be making physical contact


def main():
    vlm = OpenAIVLM(model="gpt-5.2-2025-12-11")

    # action_scene = ActionScene(
    #     who="bird",
    #     does="chases",
    #     what="puma",
    #     where=None,
    #     to_whom=None,
    # )

    # action_scene = ActionScene(
    #     who="puma",
    #     does="shows",
    #     what="bird",
    #     where=RelativeWhere(preposition="more or less in the vicinity of", what="dog"),
    #     to_whom="person",
    # )
    # # who: a puma
    # # does: shows
    # # what: a bird
    # # to whom: a person
    # # where: more or less in the vicinity of a dog
    # output_images = run(vlm, action_scene)

    # action_scene = ActionScene(
    #     who="person",
    #     does="throws",
    #     what="violin",
    #     where=None,
    #     to_whom="dog",
    # )
    # output_images = run(vlm, action_scene)

    action_scene = ActionScene(
        who="dog",
        does="tosses",
        what="chair",
        where=RelativeWhere(preposition="over", what="sign"),
        to_whom="basketball",
    )
    output_images = run(vlm, action_scene)


if __name__ == "__main__":
    main()
