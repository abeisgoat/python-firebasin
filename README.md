Python Firebasin 0.1
====================

*Please note: All "compatible" methods have been tested as functional, but not extensively. There is limited functionality for query related methods.*

Firebasin is a reimplementation of the [Firebase Javascript SDK](https://www.firebase.com/docs/javascript/firebase/index.html) in pure Python. Firebasin aims to have an interface identical to the Javascript SDK. As such, the Firebase Javascript docs can be used as temporary docs for Firebasin as the interface is identical. However, it should be noted that the implementation and internal structure of Firebasin differs greatly from the Javascript SDK. This is done intentionally as an attempt to implement things as pythonically as possible.

It is important to note that two extra methods exist on any Firebase (RootDataRef or DataRef) object exist. These methods are close() and waitForInterrupt(). These methods will shut down the websocket connection to Firebase either immediately (close()) or when a keyboard interrupt is received (waitForInterrupt()). If one of the two of these is not used the connection will stay open indefinitely. 

Compatible Method List
-----
**Firebase**
* Firebase( )			
* auth( )				
* unauth( )				
* child( )				
* parent( )				
* root( )				
* name( )				
* toString( )			
* set( )				
* update( )				
* remove( )							
* setWithPriority( )	
* setPriority( )	
* push( )		
* on( )	
* once( )		
* off( )								

**onDisconnect**
* set( )				
* setWithPriority( )	
* update( )				
* remove( )				
* cancel( )				

**DataSnapshot**
* val( )				
* child( )				
* forEach( )			
* hasChild( )			
* hasChildren( )		
* name( )				
* numChildren( )					
* getPriority( )		
* exportVal( )	
* ref( )		

Incompatible/Incomplete Method List
-----
**Firebase**	
* transaction( )
* limit( )
* startAt( )
* endAt( )	

			
