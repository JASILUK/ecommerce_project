from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework import generics
from apps.products.models import Category, Color, ProductColor, ProductColorImage, Products
from apps.products.services import ColorProductService
from apps.products.v1.permissions import IsSellerOrReadOnly
from apps.products.v1.serializers import CategoryAdminSerializer, CategorySerializer, ColorBasedVariantsListSerializer, ColorImagesListSL, ColorSerializer, CreateUpdateProductColorSL, ProductColorImageSerializer, ProductGeneralImageSerializer,  PublicProductDetailSerializer, PublicProductListSerializer, SellerCreatProductSerializer, SellerProdctsDetailedSerializer, SellerProductEditRetrieveSL, SellerProductListSerializer, SellerProductUpdateSL, createGeneralimagesSL, sellerColorBasedVariantsListSerializer
from core.permissions import IsAdmin, IsSeller
from rest_framework.filters import SearchFilter,OrderingFilter
import cloudinary
from rest_framework.decorators import action
class PublicProductsView(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'slug'

    filter_backends = [ SearchFilter, OrderingFilter]


    search_fields = ['name', 'description']

    ordering_fields = ['price', 'created_at']
    def get_queryset(self):
        queryset = Products.objects.is_active().not_blocked().prefetch_related('general_images')
        categery_slug = self.request.query_params.get('category__slug')
        if categery_slug:
            try:
                category = Category.objects.get(slug=categery_slug)
                all_category = category.get_descendants(include_self=True)
                queryset = queryset.filter(category__in=all_category)
            except:
                queryset =Products.objects.none()        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PublicProductListSerializer
        return PublicProductDetailSerializer
    

class SellerProductViewSet(viewsets.ModelViewSet):
    lookup_field = "slug"
    permission_classes = [IsSeller]

    def get_queryset(self):
        return Products.objects.by_seller(self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return SellerProductListSerializer

        if self.action == "retrieve":
            return SellerProdctsDetailedSerializer

        if self.action in  ["update" ,"create","partial_update"]:
            return SellerProductUpdateSL   

        return SellerProductListSerializer

    @action(detail=True, methods=["get"])
    def edit(self, request, *args, **kwargs):
        product = self.get_object()
        serializer = SellerProductEditRetrieveSL(product)
        return Response(serializer.data)



    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset,many=True)
        stats ={
            'total':queryset.count(),
            'active': queryset.filter(is_active=True).count(),
            'inactive':queryset.filter(is_active=False).count(),
            'blocked' : queryset.filter(is_blocked=True).count()
        }
        return Response(data={'stats':stats,'products':serializer.data},status=200)
    
    def perform_create(self, serializer):
        return serializer.save(seller = self.request.user)




class ProductColorManageView(viewsets.ModelViewSet):
    permission_classes = [IsSellerOrReadOnly]
    def get_serializer_class(self):
        if self.action =="list":
          return ColorSerializer  
        return CreateUpdateProductColorSL()
    
    def get_serializer(self, *args, **kwargs):
        serilizer = self.get_serializer()
        if self.action =='create':
            kwargs['many'] =True 
        return serilizer(*args,**kwargs)
        
    def get_product(self):
        
        return Products.objects.get(
            slug=self.kwargs["product_slug"],
            seller=self.request.user
        )
    def get_queryset(self):
        if self.action == 'list':
            return Color.objects.all()
        product = self.get_product()
        return product.product_colors.all()
  

    def perform_create(self, serializer):
        product = self.get_product()
        serializer.save(product=product)
 


class GenaralImageView(viewsets.ModelViewSet):
    permission_classes =[IsSeller]
    serializer_class = ProductGeneralImageSerializer
    def get_product(self):
        return Products.objects.get(
            slug = self.kwargs['product_slug'],
            seller =self.request.user)
        
    def get_queryset(self):
        product = self.get_product()
        return product.general_images.all()
    
    def perform_create(self, serializer):
        product = self.get_product()
        serializer.save(product=product)

 
class ColorImageManageView(viewsets.ModelViewSet):
    permission_classes = [IsSeller]
    def get_color_product(self):
        product = Products.objects.get(seller = self.request.user ,
                                       slug =self.kwargs['product_slug'])
        return ProductColor.objects.get(product = product, pk = self.kwargs['color_pk'])

    def get_queryset(self):
        color_product = self.get_color_product()
        return color_product.color_images.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ColorImagesListSL
        return ProductColorImageSerializer
    def perform_create(self, serializer):
        color_product = self.get_color_product()
        serializer.save(product_color = color_product)


class ColorBasedVariantsView(viewsets.ModelViewSet):
    def get_color_product(self):
        service = ColorProductService(
            request=self.request,
            product_slug=self.kwargs["product_slug"],
            color_pk=self.kwargs["color_pk"]
        )
        return service.get()
    
    def get_queryset(self):
        products = self.get_products()
        return products.variants.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ColorBasedVariantsListSerializer
        return sellerColorBasedVariantsListSerializer

class ListCategory(generics.ListAPIView):
    queryset = Category.objects.filter(parent__isnull =True,is_active=True)
    serializer_class = CategorySerializer

class ListAndCreateCategory(viewsets.ModelViewSet):
    lookup_field = 'slug'
    permission_classes = [IsAdmin]
    queryset = Category.objects.all
    serializer_class = CategoryAdminSerializer




class UploadFromURLAPIView(APIView):
    permission_classes =[IsSeller]
    def get_color_product(self):
        service = ColorProductService(
            request=self.request,
            product_slug=self.kwargs["product_slug"],
            color_pk=self.kwargs["color_pk"]
        )
        return service.get_color_product_service()

    def post(self, request, *args, **kwargs):
        image_url = request.data.get("image_url")
        if not image_url:
            return Response({"error": "image_url is required"}, status=400)

        result = cloudinary.uploader.upload(
            image_url,
            resource_type="image"  
        )
       
        ProductColorImage.objects.create(
            product_color=self.get_color_product(),
            image=result['public_id']
        )

        return Response({
            "image_url": result['secure_url'],
            "public_id": result['public_id']
        })