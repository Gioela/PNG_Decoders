# PNG_Decoders

The idea is do some exercises with the PNG specifications and to write a custom
 PNG decoders in different ways:

[x] Python like script

[x] Python as class

[ ] C



# Organization

In Python folder are present two different implementations of a PNG decoder:
- in scripts folder are two scripts which re-organize code from Pyokagan's Blog page[^1].
- in class folder is a script which could be imported into a project or execute from command line


# How it works

- __Python script__:

    you run the png_reader script which will read the png into the resources folder and
show it with matplotlib.pyplot lib.

    ```
    python png_decoder.py
    ```

    *NOTE*: if you want to change the png, you have to specify its path into the png_reader script row 7

- __Python class__:

    _from command line_: simply you have to specify the png image's path when you execute the python script

    ```
    python png_decoder.py png_path
    ```

    _import in a project_: import it, after you instance a PNGDecoder object, you have to declare the png input path in load_image method, then must be execute the run function

    ```
    from png_decoder import PNGDecoder

    png_interpreter = PNGDecoder()
    png_interpreter.load_image('png_path')
    png_interpreter.run()
    ```



### References:
[^1] https://pyokagan.name/blog/2019-10-14-png/