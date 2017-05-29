// -*- mode: c++-*-
/*=========================================================================

  Program:   iota2
  Language:  C++

  Copyright (c) CESBIO. All rights reserved.

  See LICENSE for details.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

=========================================================================*/

#include <cstddef>
#include <cmath>
#include <limits>
#include <vector>
#include <algorithm>
#include <functional>
#include <numeric>
#include "itkUnaryFunctorImageFilter.h"
#include "itkBinaryFunctorImageFilter.h"
#include "otbDateUtils.h"

namespace ESI
{
template<typename PixelType>
class FeatureExtractionWithMaskFunctor
{
public:
  using ValueType = typename PixelType::ValueType;
  using VectorType = typename std::vector<ValueType>;

  struct Parameters 
      {
        size_t NumberOfInputComponents{10};
	PixelType dateVector;
	size_t nbOutComp;
      };

      FeatureExtractionWithMaskFunctor() = default;
      FeatureExtractionWithMaskFunctor(Parameters pars)
	: m_NumberOfInputComponents{pars.NumberOfInputComponents},m_dateVector{pars.dateVector}{
      };
  PixelType operator () (const PixelType& pixData,const PixelType& pixMask)
      {
       PixelType result(m_NumberOfInputComponents);
       const auto inVec = VectorType(pixData.GetDataPointer(),pixData.GetDataPointer()+pixData.GetSize());
       const auto maskVec = VectorType(pixMask.GetDataPointer(),pixMask.GetDataPointer()+pixMask.GetSize());
       auto outVec = VectorType(m_NumberOfInputComponents);
       sort(inVec,maskVec,outVec);
       for (size_t i=0;i<m_NumberOfInputComponents;++i)
	 {
	   result[i]=outVec[i];
	 }
       return result;
      }
  bool operator!=(FeatureExtractionWithMaskFunctor<PixelType> f)
       {
	 return m_NumberOfInputComponents!=f.m_NumberOfInputComponents;
       }
  size_t GetNumberOfOutputComponents() const
       {
	 return m_NumberOfInputComponents;
       }
protected :
  inline
  void sort(const VectorType& inVec,const VectorType& maskVec, VectorType& outVec)
      {
	VectorType tmp;
	tmp = sort_indexes_withMask(inVec,maskVec);
	for(size_t i=0;i<m_NumberOfInputComponents;i++)
	  {
	    outVec[i]=tmp[i];
	  }
      }

  VectorType sort_indexes_withMask(const VectorType &inVec,const VectorType &maskVec)
  {

    VectorType mask;
    mask = maskVec;

    std::vector<size_t> maskedData_ind;
    VectorType  outputRes(inVec.size(),0);
    std::vector<float>::iterator iter = std::find_if(mask.begin(),mask.end(),[](float x){return x==1;});
    while (iter!=std::end(mask)){
      maskedData_ind.push_back(std::distance(std::begin(mask),iter));
      iter = std::find_if(std::next(iter),std::end(mask),[](float i){return i==1;});
    }

    size_t nbDateMasked = maskedData_ind.size();
    size_t nbDateOK = inVec.size()-nbDateMasked;

    VectorType results;
    VectorType idx(inVec.size());
    results.reserve(inVec.size());

    std::iota(idx.begin(),idx.end(),0);
    std::for_each(mask.begin(),mask.end(),[](float &n){ n=1-n; });
    std::transform(inVec.begin(),inVec.end(),mask.begin(),std::back_inserter(results),std::multiplies<float>());
    std::sort(idx.begin(),idx.end(),[&results](size_t i1,size_t i2){return results[i1] > results[i2];});
    
    for (size_t i = 0;i<nbDateOK;++i){
    outputRes[i] = m_dateVector[idx[i]];
    }

    return outputRes;
  }
  size_t m_NumberOfInputComponents;
  PixelType m_dateVector;
  size_t m_nbOutComp;

};

template <class TInputImage1,class TInputImage2, class TOutputImage,class TFunctor>
class ITK_EXPORT BinaryFunctorImageFilterWithNBands :
  public itk::BinaryFunctorImageFilter<TInputImage1, TInputImage2,
				    TOutputImage, TFunctor>
{
 public:
  typedef BinaryFunctorImageFilterWithNBands Self;
  typedef itk::BinaryFunctorImageFilter<TInputImage1,TInputImage2,TOutputImage,TFunctor> Superclass;
  typedef itk::SmartPointer<Self> Pointer;
  typedef itk::SmartPointer<const Self> ConstPointer;
  
  itkNewMacro(Self);
  itkTypeMacro(BinaryFunctorImageFilterWithNBands,Superclass);
  itkSetMacro(NumberOfOutputBands,unsigned int);
  itkGetConstMacro(NumberOfOutputBands,unsigned int);
 protected:
  BinaryFunctorImageFilterWithNBands(){}
  virtual ~BinaryFunctorImageFilterWithNBands(){}
  virtual void GenerateOutputInformation()
  {
    Superclass::GenerateOutputInformation();
    this->GetOutput()->SetNumberOfComponentsPerPixel(m_NumberOfOutputBands);
  }
 private:
  unsigned int m_NumberOfOutputBands;
};
}//end namespace extractSortedIndices

// Local Variables:
// mode: c++
// End:
