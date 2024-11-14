import argparse

import torch

def main():

    parser = argparse.ArgumentParser("Load a model using the weights-only-unpickler")
    parser.add_argument("--model_path", type=str, required=True, help="Path to the model.")

    args = parser.parse_args()

    torch.load(args.model_path, weights_only=True)

if __name__ == '__main__':
    main()
