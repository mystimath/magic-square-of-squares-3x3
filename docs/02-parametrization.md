# Paramétrisation utilisée

On considère un carré magique :

```text
a b c
d e f
h i j
````

Avec centre `e`.

Les cases opposées vérifient :

```text
a + j = 2e
b + i = 2e
c + h = 2e
d + f = 2e
```

Dans la branche v4, on impose que le centre soit un carré parfait :

```text
e = z²
```

et que deux paires opposées soient des progressions arithmétiques de carrés autour de `e`.
