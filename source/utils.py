''' From answer by user "andyhasit" on stackoverflow:
    stackoverflow.com/questions/8505163/is-it-possible-to-
    prefill-a-input-in-python-3s-command-line-interface
'''
def input_with_prefill(prompt, text):
    import readline
    def hook():
        readline.insert_text(text)
        readline.redisplay()
    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result

