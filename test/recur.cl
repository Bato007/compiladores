class Fibonacci {
  	
  	fibonacci(n: Int) : Int {
        {( let f : Int in
      	 if n=1 then f<-1 else
         if n=2 then f<-1 else
        	 f<-fibonacci(n-1)+fibonacci(n-2)
         fi fi
       );}
     };
  
  };

class Main inherits IO {
    n: Int <- 3;
  	fibo: Fibonacci;
  
  	main() : SELF_TYPE {
	{
      	fibo <- new Fibonacci;
      	--out_int(facto.factorial(n));
      	out_int(fibo.fibonacci(n));
      	self;
	}
    };
};
