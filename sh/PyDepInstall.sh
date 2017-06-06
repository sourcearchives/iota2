# Installation des dépendances pythons
LISTE="argparse config datetime numpy scipy osr matplotlib cPickle"

for i in $LISTE; do 
  echo $i;
  pip install --install-option="--prefix=/data/OSO/python/" $i
done

