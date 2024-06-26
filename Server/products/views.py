from django.http import JsonResponse
from .forms import ProductForm, CommentForm
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.permissions import IsAdminUser
from .models import Product,Comment1,Cart1
from .serializers import ProductSerializer,CommentSerializer,ProductUpdateSerializer,CartSerializer,ProductQuantityUpdateSerializer
from rest_framework import generics, status

class AddProductView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.uploaded_by = request.user.name
            product.save()
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})

class ProductListView(APIView):
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)

        # Fetch comments for each product
        for product in serializer.data:
            comments = Comment1.objects.filter(product_id=product['id'])
            comment_serializer = CommentSerializer(comments, many=True)
            product['comments'] = comment_serializer.data

        return Response(serializer.data)

class FarmerProductListView(APIView):
    permission_classes = [ IsAdminUser]

    def get(self, request):
        # Fetch products uploaded by the authenticated user
        products = Product.objects.filter(uploaded_by=request.user.name)
        serializer = ProductSerializer(products, many=True)

        # Fetch comments for each product
        for product in serializer.data:
            comments = Comment1.objects.filter(product_id=product['id'])
            comment_serializer = CommentSerializer(comments, many=True)
            product['comments'] = comment_serializer.data

        return Response(serializer.data)

class CommentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.name = request.user.name
            comment.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})


class ProductDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated,IsAdminUser]
    queryset = Product.objects.all() 
    serializer_class = ProductSerializer

    def delete(self, request, *args, **kwargs):
        product = self.get_object()

        # if product.uploaded_by != self.request.user.name:
        #     return Response({'error': 'You are not authorized to delete this product.'}, status=status.HTTP_401_UNAUTHORIZED)

        carts = Cart1.objects.filter(product=product)
        # Delete the carts containing the product
        carts.delete()
        # Delete the comments associated with the product
        comments = Comment1.objects.filter(product_id=product.id)
        comments.all().delete()

        # Delete the product itself
        product.delete()

        return Response({'message': 'Product deleted successfully.'}, status=status.HTTP_200_OK)



class ProductUpdateView(generics.UpdateAPIView):
    permission_classes = [ IsAdminUser]
    queryset = Product.objects.all()
    serializer_class = ProductUpdateSerializer

    def patch(self, request, *args, **kwargs):
        product = self.get_object()

        # Check if the user updating the product is the same as the user who uploaded it
        # if request.user.name != product.uploaded_by:
        #     return Response({'error': 'You are not authorized to update this product.'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.serializer_class(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Product Updated successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductQuantityUpdateView(generics.UpdateAPIView):
    # permission_classes = [IsAdminUser]
    queryset = Product.objects.all()
    serializer_class = ProductQuantityUpdateSerializer

    def patch(self, request, *args, **kwargs):
        product = self.get_object()

        serializer = self.serializer_class(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Product quantity updated successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


        
#Cart
class AddToCartView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer
    
    def post(self, request, *args, **kwargs):
        product_id = request.data.get('product_id', None)
        quantity = request.data.get('quantity', 1)

        # Check if the product exists
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Create or update the cart item
        user_id = request.user.id
        cart_item, created = Cart1.objects.get_or_create(
            user_id=user_id,
            product_id=product_id,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += int(quantity)
            cart_item.save()
        
        serializer = CartSerializer(cart_item)
        return Response({'msg': 'Added to Cart'}, status=status.HTTP_200_OK)

class CartListView(APIView):
    def get(self, request):
        user_id = request.user.id
        cart_items = Cart1.objects.filter(user_id=user_id)
        serializer = CartSerializer(cart_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CartDeleteView(generics.DestroyAPIView):
    serializer_class = CartSerializer
    queryset = Cart1.objects.all()

    def delete(self, request, *args, **kwargs):
        cart_item = self.get_object()

        if cart_item.user != request.user:
            return Response({'error': 'You are not authorized to delete this item from the cart.'}, status=status.HTTP_401_UNAUTHORIZED)

        cart_item.delete()
        return Response({'message': 'Item deleted successfully from the cart.'}, status=status.HTTP_200_OK)
    
from .models import Order
from .forms import OrderForm
    
class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.ordered_by = request.user.name
            order.save()
            return JsonResponse({'id': order.id}, status=201)
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
from django.shortcuts import get_object_or_404

class OrderDeleteView(APIView):
    def delete(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        order.delete()
        return JsonResponse({'success': True}, status=200)

from django.db.models import Max
from django.http import JsonResponse
from .models import Order


# class RecentOrdersView(APIView):
#     def get(self, request):
#         # get the latest order id for each created_by value
#         subquery = Order.objects.values('ordered_by').annotate(latest_order_id=Max('id'))
#         # filter the orders by the latest order id for each created_by value
#         orders = Order.objects.filter(id__in=subquery.values('latest_order_id'))

#         # serialize the orders
#         serialized_orders = []
#         for order in orders:
#             serialized_order = {
#                 'id': order.id,
#                 'ordered_by': order.ordered_by,
#                 'order_item': order.order_item,
#                 'created_at': order.created_at,
#                 'order_quantity':order.order_quantity,
#             }
#             serialized_orders.append(serialized_order)

#         return JsonResponse(serialized_orders,safe=False)

from django.utils import timezone
from datetime import timedelta

class RecentOrdersView(APIView):
    def get(self, request):
        # calculate the datetime for 24 hours ago
        yesterday = timezone.now() - timedelta(hours=24)

        # filter the orders by the created_at timestamp within the last 24 hours
        orders = Order.objects.filter(created_at__gte=yesterday)

        # serialize the orders
        serialized_orders = []
        for order in orders:
            serialized_order = {
                'id': order.id,
                'ordered_by': order.ordered_by,
                'order_item': order.order_item,
                'created_at': order.created_at,
                'order_quantity':order.order_quantity,
            }
            serialized_orders.append(serialized_order)

        return JsonResponse(serialized_orders, safe=False)


