ECHO OFF

FOR /L %%i IN (1,1,100000) DO (
    python exp_MNIST_full.py --run %%i --jul_threading 4 --digits 10 --samples 50 --name MNIST_large --low_bound 0 --eta 0.0005 --decay True
)

PAUSE
