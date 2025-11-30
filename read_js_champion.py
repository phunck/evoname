def main():
    try:
        with open("dist/evoname.js", "r", encoding="utf-8") as f:
            content = f.read()
            # Find the champion function
            start = content.find("function champion(raw_input) {")
            if start == -1:
                print("Champion function not found")
                return
            end = content.find("}", start) + 1
            print(content[start:end+200]) # Print a bit more context
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
