# Basics in Python

# Etwas in der Konsole ausgeben: print
print("Hallo, hier ist Luca")

# if-Verzweigungen: if Bedingung:
if __name__ == "__main__":
    # Eingerückt: action
    print("Das ist ein Test")

# Variablen deklarieren: name = Wert
ani = "ANI"
print(ani)

# Comment: # Kommentar

# Mehrzeilige Kommentare: """ Kommentar """
"""
Hallo
Test
Guten Tag
Das ist ein Test
"""

# Ausgabe mit mehreren Parametern: print(param1, param2) -> Ausgabe mit Leerzeichen
print("Hello", "World") # => "Hello World"

# Ausgabe mehrer Dinge mit '+' -> Ausgabe ohne Leerzeichen
a = 'Hello'
b = 'World'
print(a + b) # => "HelloWorld"

# Lists
liste = [1, 2, 3, 4, 5]
print(liste) # => [1, 2, 3, 4, 5]

liste.append(6) # fügt etwas am Ende hinzu => [1, 2, 3, 4, 5, 6]
liste.remove(1) # entfernt die Sache => [2, 3, 4, 5, 6]
liste.index(2) # gibt die Position der Sache aus (ab 0 zählen) => 0
liste.pop(0) # gibt die Sache an der Position aus (am 0 zählen) => 2
liste.extend([7, 8, 9]) # fügt die Sachen an die Liste an => [3, 4, 5, 6, 7, 8, 9]

# Tuples
tupel = (1, 2, 3, 4, 5)
print(tupel) # => (1, 2, 3, 4, 5)

tupel.index(2) # gibt die Position der Sache aus (ab 0 zählen) => 1
tupel.index(2, 1) # gibt die Position der Sache aus (ab 0 zählen) => 1

# Dictionaries
dict = {"key1": "value1", "key2": "value2"}
print(dict) # => {"key1": "value1", "key2": "value2"}

dict.update({"key3": "value3"}) # fügt einen neuen Key hinzu => {"key1": "value1", "key2": "value2", "key3": "value3"}
dict["key1"] = "new_value" # ändert den Wert des Keys => {"key1": "new_value", "key2": "value2", "key3": "value3"}
dict.pop("key1") # entfernt den Key => {"key2": "value2", "key3": "value3"}

# Difference List und Tuple: 
# List ist veränderbar, Tuple nicht
# List ist in [] und Tuple in ()
# Dictionaries sind in {}


zahl = 1
zahl2 = 2.2
zahl3 = (int(zahl2)) # wandelt die Zahl in eine int um

string1 = "Hallo"
print(string1[2]) # gibt den Buchstaben an der Stelle 2 aus => "l"
print(len(string1)) # gibt die Länge des Strings aus => 5