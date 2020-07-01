# -*- coding: utf-8 -*-
"""starter_gmm.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1N8-it2YMcR7vSeyVRk5dA8IrLSa2Wus7
"""

import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import helper as hlp

# Loading data
data = np.load('data100D.npy')
#data = np.load('data2D.npy')
[num_pts, dim] = np.shape(data)
print([num_pts, dim])

# For Validation set
if is_valid:
  valid_batch = int(num_pts / 3.0)
  np.random.seed(45689)
  rnd_idx = np.arange(num_pts)
  np.random.shuffle(rnd_idx)
  val_data = data[rnd_idx[:valid_batch]]
  data = data[rnd_idx[valid_batch:]]

# Distance function for GMM
def distanceFunc(X, MU):
  # Inputs
  # X: is an NxD matrix (N observations and D dimensions)
  # MU: is an KxD matrix (K means and D dimensions)
  # Outputs
  # pair_dist: is the pairwise distance matrix (NxK)
  # TODO
  X_X = tf.reshape(tf.reduce_sum(tf.square(X), axis=1), [-1, 1])
  MU_MU = tf.reshape(tf.reduce_sum(tf.square(MU), axis=1), [1, -1])
  X_MU = (-2) * tf.matmul(X, tf.transpose(MU))
  return X_X + MU_MU + X_MU

def log_GaussPDF(X, mu, sigma):
    # Inputs
    # X: N X D
    # mu: K X D
    # sigma: K X 1, passed in as sigma^2

    # Outputs:
    # log Gaussian PDF N X K
    
    # TODO
    dim = tf.to_float(tf.rank(X)) #convert to correct data type
    sigma = tf.squeeze(sigma)
    dist = distanceFunc(X, mu)
    exp = (-1) * dist / (2 * sigma)
    coeff = (-1) * (dim/2) * tf.log(2*np.pi * sigma)
    return coeff + exp

def log_posterior(log_PDF, log_pi):
    # Input
    # log_PDF: log Gaussian PDF N X K
    # log_pi: K X 1

    # Outputs
    # log_post: N X K

    # TODO
    log_post = log_PDF + tf.transpose(log_pi)
    log_sum = reduce_logsumexp(log_post,keep_dims=True)
    return log_post - log_sum

def MoG(k, learning_rate,):
  tf.set_random_seed(421)
  K = k
  N = num_pts
  D = dim

  X = tf.placeholder(tf.float32, shape=(None,D), name="X")
  MU = tf.get_variable("MU", initializer=tf.random.normal(shape=[K,D]))
  sigma = tf.get_variable("sigma", initializer=tf.random.normal(shape=[K, 1]))
  sigma = tf.exp(sigma)
  pi = tf.get_variable("pi", initializer=tf.random.normal(shape=[K, 1]))
  log_pi = tf.squeeze(logsoftmax(pi))
  log_PDF = log_GaussPDF(X, MU, sigma)
  #log_post = log_posterior(log_PDF, log_pi)
  #log_post = log_PDF + log_post
  log_post = log_PDF + log_pi
  clusters = tf.argmax(tf.nn.softmax(log_posterior(log_PDF, log_pi)), 1)

  loss = (-1) * tf.reduce_sum(reduce_logsumexp(log_post))
  optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate, beta1=0.9, beta2=0.99, epsilon=1e-5).minimize(loss)
  
  return X, MU, sigma, pi, loss, optimizer, clusters

def train(learning_rate=0.1, epoch=500, k=3, is_valid=False):
  if is_valid:
    valid_batch = int(num_pts / 3.0)
    np.random.seed(45689)
    rnd_idx = np.arange(num_pts)
    np.random.shuffle(rnd_idx)
    val_data = data[rnd_idx[:valid_batch]]
    train_data = data[rnd_idx[valid_batch:]]
  else:
    train_data = data

  train_loss = np.zeros(epoch)
  valid_loss = np.zeros(epoch)
  cls = np.zeros(epoch)

  tf.reset_default_graph() 
  [X, MU, sigma, pi, loss, optimizer, clusters] = MoG(k, learning_rate)

  with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    sess.run(tf.local_variables_initializer())
    for i in range(epoch):
      train_current_MU,train_current_sigma,train_current_pi,train_current_loss,_,cls = sess.run([MU,sigma,pi,loss,optimizer,clusters], feed_dict={X:train_data})
      train_loss[i] = train_current_loss

      if is_valid:
          valid_current_MU,valid_current_sigma,valid_current_pi,valid_current_loss,_,_ = sess.run([MU,sigma,pi,loss,optimizer,clusters], feed_dict={X:val_data})
          valid_loss[i] = valid_current_loss

    final_MU = train_current_MU
    final_sigma = train_current_sigma
    final_pi = train_current_pi

  #log_pi = logsoftmax(final_pi)
  #log_PDF = log_GaussPDF(train_data, final_MU, final_sigma)
  clusters = cls

  #print("Final Model Parameterss are: ")
  #print(" u = ",final_MU)
  #print(" sigma = ",final_sigma)
  #print(" pi = ",final_pi)
  print("Final Training Loss is: ", train_loss[epoch-1])
  print("Final Validation Loss is: ", valid_loss[epoch-1])
  plt.figure(1)
  plt.plot(range(len(train_loss)),train_loss,label="Train Loss")
  plt.plot(range(len(train_loss)),valid_loss,label="Validation Loss")
  plt.legend(loc = "best")
  plt.title('MoG Train Loss')
  plt.xlabel('Epoch')
  plt.ylabel('Loss')
  plt.show()

  k = len(final_MU)
  plt.scatter(train_data[:, 0], train_data[:, 1], c=clusters, 
              cmap=plt.get_cmap('Set3'), s=25, alpha=0.6)
  plt.scatter(final_MU[:, 0], final_MU[:, 1], marker='*', c="black", 
              cmap=plt.get_cmap('Set1'), s=50, linewidths=1)
  plt.title('MoG Clusters')
  plt.xlabel('X')
  plt.ylabel('Y')
  plt.grid()
  plt.show()
  
  return valid_loss

train(learning_rate=0.1, epoch=500, k=3, is_valid=False)

train(learning_rate=0.1, epoch=1000, k=3, is_valid=False)

k1_valid_loss = train(learning_rate=0.1, epoch=1000, k=1, is_valid=True)
k2_valid_loss = train(learning_rate=0.1, epoch=1000, k=2, is_valid=True)
k3_valid_loss = train(learning_rate=0.1, epoch=1000, k=3, is_valid=True)
k4_valid_loss = train(learning_rate=0.1, epoch=1000, k=4, is_valid=True)
k5_valid_loss = train(learning_rate=0.1, epoch=1000, k=5, is_valid=True)

plt.plot(range(len(k1_valid_loss)),k1_valid_loss,label="k=1")
plt.plot(range(len(k2_valid_loss)),k2_valid_loss,label="k=2")
plt.plot(range(len(k3_valid_loss)),k3_valid_loss,label="k=3")
plt.plot(range(len(k4_valid_loss)),k4_valid_loss,label="k=4")
plt.plot(range(len(k5_valid_loss)),k5_valid_loss,label="k=5")
plt.legend(loc = "best")
plt.title('Mog Validation Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.show()

k5_valid_loss = train(learning_rate=0.1, epoch=1000, k=5, is_valid=True)
k10_valid_loss = train(learning_rate=0.1, epoch=1000, k=10, is_valid=True)
k15_valid_loss = train(learning_rate=0.1, epoch=1000, k=15, is_valid=True)
k20_valid_loss = train(learning_rate=0.1, epoch=1000, k=20, is_valid=True)
k30_valid_loss = train(learning_rate=0.1, epoch=1000, k=30, is_valid=True)

plt.plot(range(len(k5_valid_loss)),k5_valid_loss,label="k=5")
plt.plot(range(len(k10_valid_loss)),k10_valid_loss,label="k=10")
plt.plot(range(len(k15_valid_loss)),k15_valid_loss,label="k=15")
plt.plot(range(len(k20_valid_loss)),k20_valid_loss,label="k=20")
plt.plot(range(len(k30_valid_loss)),k30_valid_loss,label="k=30")
plt.legend(loc = "best")
plt.title('Mog Validation Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.show()

def reduce_logsumexp(input_tensor, reduction_indices=1, keep_dims=False):
  """Computes the sum of elements across dimensions of a tensor in log domain.

     It uses a similar API to tf.reduce_sum.

  Args:
    input_tensor: The tensor to reduce. Should have numeric type.
    reduction_indices: The dimensions to reduce. 
    keep_dims: If true, retains reduced dimensions with length 1.
  Returns:
    The reduced tensor.
  """
  max_input_tensor1 = tf.reduce_max(
      input_tensor, reduction_indices, keep_dims=keep_dims)
  max_input_tensor2 = max_input_tensor1
  if not keep_dims:
    max_input_tensor2 = tf.expand_dims(max_input_tensor2, reduction_indices)
  return tf.log(
      tf.reduce_sum(
          tf.exp(input_tensor - max_input_tensor2),
          reduction_indices,
          keep_dims=keep_dims)) + max_input_tensor1

def logsoftmax(input_tensor):
  """Computes normal softmax nonlinearity in log domain.

     It can be used to normalize log probability.
     The softmax is always computed along the second dimension of the input Tensor.     

  Args:
    input_tensor: Unnormalized log probability.
  Returns:
    normalized log probability.
  """
  return input_tensor - reduce_logsumexp(input_tensor, reduction_indices=0, keep_dims=True)